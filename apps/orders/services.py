from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.catalog.models import LicenseType, Product
from apps.catalog.selectors import is_offer_available
from apps.orders.models import LicenseGrant, Order, OrderItem, PaymentAttempt
from apps.orders.policies import (
    UnresolvedLicenseIdentity,
    ensure_complete_license_conditions,
    ensure_license_not_owned,
)


class EmptyCart(Exception):
    pass


class OfferNotAvailable(Exception):
    pass


class InvalidPaymentInput(Exception):
    pass


class PaymentConflict(Exception):
    pass


class LegacyDocumentationConflict(Exception):
    pass


@transaction.atomic
def create_order_from_cart(*, owner) -> Order:
    try:
        cart = Cart.objects.select_for_update().get(owner=owner)
    except Cart.DoesNotExist:
        raise EmptyCart from None
    cart_items = list(
        CartItem.objects.select_for_update()
        .filter(cart=cart)
        .select_related("offer__product__category", "offer__license_type")
    )
    if not cart_items:
        raise EmptyCart
    if any(not is_offer_available(item.offer) for item in cart_items):
        raise OfferNotAvailable
    for item in cart_items:
        ensure_complete_license_conditions(
            terms_version=item.offer.license_type.terms_version,
            terms_text=item.offer.license_type.terms_text,
            usage_scope=item.offer.license_type.usage_scope,
            grantor_name=item.offer.grantor_name,
            rights_holder_name=item.offer.rights_holder_name,
        )

        ensure_license_not_owned(
            owner=owner,
            product=item.offer.product,
            license_type=item.offer.license_type,
        )
    total_amount = sum((item.offer.price for item in cart_items), Decimal("0.00"))
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=total_amount,
    )
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                source_product=item.offer.product,
                source_license_type=item.offer.license_type,
                product_sku=item.offer.product.sku,
                product_name=item.offer.product.name,
                license_name=item.offer.license_type.name,
                terms_version=item.offer.license_type.terms_version,
                terms_text=item.offer.license_type.terms_text,
                usage_scope=item.offer.license_type.usage_scope,
                grantor_name=item.offer.grantor_name,
                rights_holder_name=item.offer.rights_holder_name,
                price=item.offer.price,
                currency=item.offer.currency,
            )
            for item in cart_items
        ]
    )
    CartItem.objects.filter(cart=cart).delete()
    return order


@transaction.atomic
def approve_simulated_payment(
    *,
    owner,
    order_id,
    result,
    idempotency_key,
) -> PaymentAttempt:
    # Coordinar los pagos de distintos pedidos del mismo cliente.
    get_user_model().objects.select_for_update().get(pk=owner.pk)

    # Obtener y bloquear el pedido del propietario.
    order = Order.objects.select_for_update().get(
        pk=order_id,
        owner=owner,
    )

    # Admitir aprobación y rechazo simulados.
    if result not in (
        PaymentAttempt.Result.APPROVED,
        PaymentAttempt.Result.FAILED,
    ):
        raise InvalidPaymentInput

    try:
        payment_key = UUID(str(idempotency_key))
    except ValueError:
        raise InvalidPaymentInput from None

    previous_attempt = PaymentAttempt.objects.filter(
        order=order, idempotency_key=payment_key
    ).first()

    # Si ya existe ese intento con el mismo resultado, devolverlo sin escribir nada.
    if previous_attempt is not None:
        if previous_attempt.result != result:
            raise PaymentConflict
        return previous_attempt

    # Una clave nueva solo puede utilizarse en un pedido pendiente.
    if order.status != Order.Status.PENDING_PAYMENT:
        raise PaymentConflict

    # Comprobar la recompra antes de registrar una nueva aprobación.
    if result == PaymentAttempt.Result.APPROVED:
        order_items = OrderItem.objects.filter(order=order).select_related(
            "source_product",
            "source_license_type",
        )

        for item in order_items:
            # Validar las condiciones históricas del pedido.
            ensure_complete_license_conditions(
                terms_version=item.terms_version,
                terms_text=item.terms_text,
                usage_scope=item.usage_scope,
                grantor_name=item.grantor_name,
                rights_holder_name=item.rights_holder_name,
            )

            # Impedir el pago cuando no se puede identificar la combinación.
            if item.source_product is None or item.source_license_type is None:
                raise UnresolvedLicenseIdentity(
                    "El pedido necesita revisión: contiene líneas sin identificar."
                )

            ensure_license_not_owned(
                owner=owner,
                product=item.source_product,
                license_type=item.source_license_type,
            )

    # Registrar el resultado con el importe y moneda históricos.
    attempt = PaymentAttempt.objects.create(
        order=order,
        idempotency_key=payment_key,
        result=result,
        amount=order.total_amount,
        currency=order.currency,
    )

    # Marca el pedido como pagado, recupera sus lineas historicas y crea un derecho activo a cada linea.
    if result == PaymentAttempt.Result.APPROVED:
        order.status = Order.Status.PAID
        order.save(update_fields=["status"])

        for order_item in OrderItem.objects.filter(order=order):
            LicenseGrant.objects.create(
                order_item=order_item,
                status=LicenseGrant.Status.ACTIVE,
            )

    return attempt


@transaction.atomic
def regularize_paid_order_grants(*, order_ids) -> int:
    """Crear permisos faltantes para los pedidos pagados seleccionados."""
    order_ids = tuple(order_ids)
    created_count = 0

    # Identificar los propietarios de los pedidos seleccionados.
    owner_ids = Order.objects.filter(
        pk__in=order_ids,
    ).values_list("owner_id", flat=True)

    # Usar el mismo bloqueo por propietario que la aprobación del pago.
    owners = (
        get_user_model()
        .objects.select_for_update()
        .filter(pk__in=owner_ids)
        .order_by("pk")
    )

    for owner in owners:
        # Procesar únicamente pedidos seleccionados que ya estén pagados.
        paid_orders = (
            Order.objects.select_for_update()
            .filter(
                pk__in=order_ids,
                owner=owner,
                status=Order.Status.PAID,
            )
            .order_by("pk")
        )

        for order in paid_orders:
            items = OrderItem.objects.filter(order=order).order_by("pk")

            for item in items:
                # Conservar el permiso existente o crear el que falta.
                _, created = LicenseGrant.objects.get_or_create(
                    order_item=item,
                    defaults={"status": LicenseGrant.Status.ACTIVE},
                )

                if created:
                    created_count += 1

    return created_count


@transaction.atomic
def regularize_legacy_order_item(*, order_item_id, mappings):
    """Completar datos ausentes mediante una única correspondencia revisada."""
    mappings = list(mappings)

    # Exigir una correspondencia única y dirigida a esta línea.
    if len(mappings) != 1:
        raise LegacyDocumentationConflict(
            "Debe existir exactamente una correspondencia histórica."
        )

    mapping = mappings[0]

    if mapping.get("order_item_id") != order_item_id:
        raise LegacyDocumentationConflict(
            "La correspondencia pertenece a otra línea de pedido."
        )

    # Comprobar que se identifica el respaldo documental y su revisión.
    evidence = mapping.get("evidence_reference")
    reviewed_at = mapping.get("reviewed_at")
    reviewer_id = mapping.get("reviewed_by_id")

    if not isinstance(evidence, str) or not evidence.strip():
        raise LegacyDocumentationConflict("Falta la referencia al documento histórico.")

    if (
        not isinstance(reviewed_at, datetime)
        or timezone.is_naive(reviewed_at)
        or reviewed_at > timezone.now()
    ):
        raise LegacyDocumentationConflict("Falta una fecha de revisión válida.")

    if (
        not get_user_model()
        .objects.filter(
            pk=reviewer_id,
            is_active=True,
            is_staff=True,
        )
        .exists()
    ):
        raise LegacyDocumentationConflict(
            "La revisión debe identificar a un administrador activo."
        )

    # Coordinar la operación con pagos y otras regularizaciones.
    reference = (
        OrderItem.objects.filter(pk=order_item_id)
        .values(
            "order_id",
            "order__owner_id",
        )
        .get()
    )

    get_user_model().objects.select_for_update().get(
        pk=reference["order__owner_id"],
    )
    order = Order.objects.select_for_update().get(
        pk=reference["order_id"],
    )
    item = OrderItem.objects.select_for_update().get(
        pk=order_item_id,
        order=order,
    )

    if order.status != Order.Status.PAID:
        raise LegacyDocumentationConflict(
            "Esta operación solo regulariza compras ya pagadas."
        )

    # Validar las referencias explícitas, sin buscar por nombre ni SKU.
    references = (
        ("source_product", Product),
        ("source_license_type", LicenseType),
    )
    changes = {}

    for field, model in references:
        proposed_id = mapping.get(f"{field}_id")

        if not isinstance(proposed_id, int) or isinstance(proposed_id, bool):
            raise LegacyDocumentationConflict(
                f"Falta una referencia válida para {field}."
            )

        if not model.objects.filter(pk=proposed_id).exists():
            raise LegacyDocumentationConflict(
                f"La referencia indicada para {field} no existe."
            )

        current_id = getattr(item, f"{field}_id")

        if current_id is None:
            changes[field] = proposed_id
        elif current_id != proposed_id:
            raise LegacyDocumentationConflict(
                f"La correspondencia contradice la referencia {field}."
            )

    # Validar todo el documento antes de modificar la línea.
    condition_fields = (
        "terms_version",
        "terms_text",
        "usage_scope",
        "grantor_name",
        "rights_holder_name",
    )

    for field in condition_fields:
        proposed_value = mapping.get(field)

        if not isinstance(proposed_value, str) or not proposed_value.strip():
            raise LegacyDocumentationConflict(
                f"La documentación histórica no contiene {field}."
            )

        current_value = getattr(item, field)

        if not current_value.strip():
            changes[field] = proposed_value
        elif current_value != proposed_value:
            raise LegacyDocumentationConflict(
                f"La documentación contradice el valor histórico de {field}."
            )

    # Guardar únicamente los campos ausentes; repetir no provoca escrituras.
    if changes:
        for field, value in changes.items():
            if field in ("source_product", "source_license_type"):
                setattr(item, f"{field}_id", value)
            else:
                setattr(item, field, value)

        item.save(update_fields=list(changes))

    return item
