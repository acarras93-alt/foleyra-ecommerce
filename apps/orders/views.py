from functools import wraps
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_POST

from apps.cart.selectors import get_cart_summary
from apps.catalog.models import private_master_storage
from apps.orders.models import LicenseGrant, Order, PaymentAttempt
from apps.orders.policies import (
    IncompleteLicenseConditions,
    LicenseAlreadyOwned,
    UnresolvedLicenseIdentity,
)
from apps.orders.selectors import get_order_for_owner, get_orders_for_owner
from apps.orders.services import (
    EmptyCart,
    InvalidPaymentInput,
    MasterNotPrepared,
    OfferNotAvailable,
    PaymentConflict,
    approve_simulated_payment,
    create_order_from_cart,
)


def order_write_login_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('users:login')}?next={reverse('cart:detail')}")
        return view_func(request, *args, **kwargs)

    return wrapped


def order_read_login_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('users:login')}?next={request.path}")
        return view_func(request, *args, **kwargs)

    return wrapped


@require_GET
@order_read_login_required
def order_list(request):
    orders = get_orders_for_owner(owner=request.user)
    return render(request, "orders/order_list.html", {"orders": orders})


@require_GET
@order_read_login_required
def order_detail(request, order_id):
    try:
        order = get_order_for_owner(
            owner=request.user,
            order_id=order_id,
        )
    except Order.DoesNotExist:
        raise Http404("Pedido no encontrado") from None

    payment_key = uuid4() if order.status == Order.Status.PENDING_PAYMENT else None

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "payment_key": payment_key,
        },
    )


@require_POST
@order_write_login_required
def create_order(request):
    try:
        create_order_from_cart(owner=request.user)
    except EmptyCart:
        error_message = "Tu carrito está vacío."
    except OfferNotAvailable:
        error_message = "No se puede crear el pedido porque una de las ofertas ya no está disponible."
    except MasterNotPrepared:
        error_message = (
            "No se puede crear el pedido porque uno de los sonidos no tiene "
            "su archivo maestro preparado. Tu carrito se conserva. "
            "Puedes seguir comprando o intentarlo más tarde."
        )
    except (
        LicenseAlreadyOwned,
        IncompleteLicenseConditions,
        UnresolvedLicenseIdentity,
    ) as error:
        error_message = str(error)
    else:
        messages.success(request, "Pedido creado.")
        return redirect("cart:detail")

    return render(
        request,
        "cart/cart_detail.html",
        {
            "cart_summary": get_cart_summary(owner=request.user),
            "checkout_error": error_message,
        },
        status=409,
    )


@require_POST
def simulate_payment(request, order_id):
    if not request.user.is_authenticated:
        detail_url = reverse(
            "orders:detail",
            kwargs={"order_id": order_id},
        )
        return redirect(f"{reverse('users:login')}?next={detail_url}")

    allowed_fields = {
        "result",
        "idempotency_key",
        "csrfmiddlewaretoken",
    }

    try:
        if set(request.POST) - allowed_fields:
            get_order_for_owner(owner=request.user, order_id=order_id)
            return HttpResponse(status=400)

        attempt = approve_simulated_payment(
            owner=request.user,
            order_id=order_id,
            result=request.POST.get("result"),
            idempotency_key=request.POST.get("idempotency_key"),
        )

    except Order.DoesNotExist:
        raise Http404("Pedido no encontrado") from None
    except InvalidPaymentInput:
        return HttpResponse(status=400)
    except (PaymentConflict, MasterNotPrepared):
        return HttpResponse(status=409)
    except (
        LicenseAlreadyOwned,
        IncompleteLicenseConditions,
        UnresolvedLicenseIdentity,
    ) as error:
        return HttpResponse(str(error), status=409)

    if attempt.result == PaymentAttempt.Result.APPROVED:
        messages.success(request, "Pago simulado aprobado.")
    else:
        messages.error(request, "Pago simulado rechazado.")

    return redirect("orders:detail", order_id=order_id)


@require_GET
@login_required
def license_list(request):
    # Consultar los permisos activos de los pedidos pagados del usuario.
    grants = (
        LicenseGrant.objects.filter(
            order_item__order__owner=request.user,
            order_item__order__status=Order.Status.PAID,
            status=LicenseGrant.Status.ACTIVE,
        )
        .select_related("order_item__order")
        .order_by("-issued_at", "-pk")
    )

    # Mostrar los permisos y los datos históricos de sus líneas.
    return render(
        request,
        "orders/license_list.html",
        {"grants": grants},
    )


@require_GET
@login_required
def license_detail(request, license_id):
    # Obtener únicamente un permiso del usuario autenticado.
    grant = get_object_or_404(
        LicenseGrant.objects.select_related("order_item__order"),
        pk=license_id,
        order_item__order__owner=request.user,
    )

    # Leer las condiciones históricas de la línea comprada.
    item = grant.order_item

    has_documented_terms = all(
        value.strip()
        for value in (
            item.terms_version,
            item.terms_text,
            item.usage_scope,
            item.grantor_name,
            item.rights_holder_name,
        )
    )

    can_download = bool(
        grant.status == LicenseGrant.Status.ACTIVE
        and item.order.status == Order.Status.PAID
        and item.master_preparation_id
    )

    # Mostrar el detalle sin reconstruir condiciones desde el catálogo.
    return render(
        request,
        "orders/license_detail.html",
        {
            "grant": grant,
            "item": item,
            "has_documented_terms": has_documented_terms,
            "can_download": can_download,
        },
    )


@require_GET
@login_required
def license_download(request, license_id):
    # Autorizar únicamente un derecho propio, activo y de un pedido pagado.
    grant = (
        LicenseGrant.objects.filter(
            pk=license_id,
            order_item__order__owner=request.user,
            order_item__order__status=Order.Status.PAID,
            status=LicenseGrant.Status.ACTIVE,
        )
        .select_related(
            "order_item__order",
            "order_item__master_preparation",
        )
        .first()
    )

    if grant is None:
        raise Http404("Archivo no disponible.")

    # Resolver el maestro histórico de la línea comprada.
    item = grant.order_item
    preparation = item.master_preparation

    if preparation is None:
        raise Http404("Archivo no disponible.")

    content_type = {
        "wav": "audio/wav",
        "flac": "audio/flac",
        "aiff": "audio/aiff",
    }.get(preparation.audio_format)

    if content_type is None:
        raise Http404("Archivo no disponible.")

    # Construir un nombre público a partir del nombre histórico.
    public_name = slugify(item.product_name)[:100] or "sonido"
    filename = f"{public_name}.{preparation.audio_format}"

    # Abrir únicamente la clave guardada en la preparación.
    try:
        stored = private_master_storage.open(
            preparation.storage_key,
            "rb",
        )
    except OSError:
        raise Http404("Archivo no disponible.") from None

    # FileResponse envía los bytes y gestiona el cierre del archivo.
    response = FileResponse(
        stored,
        as_attachment=True,
        filename=filename,
        content_type=content_type,
    )
    response["Cache-Control"] = "private, no-store"

    return response
