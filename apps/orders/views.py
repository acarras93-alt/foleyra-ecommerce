from functools import wraps

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

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


@require_POST
@order_write_login_required
def create_order(request):
    try:
        create_order_from_cart(owner=request.user)
    except (EmptyCart, OfferNotAvailable):
        return HttpResponse(status=409)
    messages.success(request, "Pedido creado.")
    return redirect("cart:detail")
