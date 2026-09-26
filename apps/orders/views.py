from functools import wraps

from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from apps.orders.models import Order
from apps.orders.selectors import get_order_for_owner, get_orders_for_owner
from apps.orders.services import (
    EmptyCart,
    OfferNotAvailable,
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
        order = get_order_for_owner(owner=request.user, order_id=order_id)

    except Order.DoesNotExist:
        raise Http404("Pedido no encontrado") from None

    return render(
        request,
        "orders/order_detail.html",
        {"order": order},
    )


@require_POST
@order_write_login_required
def create_order(request):
    try:
        create_order_from_cart(owner=request.user)
    except (EmptyCart, OfferNotAvailable):
        return HttpResponse(status=409)
    messages.success(request, "Pedido creado.")
    return redirect("cart:detail")
