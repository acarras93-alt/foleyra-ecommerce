from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.cart.selectors import get_cart_summary
from apps.cart.services import (
    CartItemNotFound,
    OfferNotAvailable,
    add_offer_to_cart,
    remove_cart_item,
)
from apps.orders.policies import (
    LicenseAlreadyOwned,
    UnresolvedLicenseIdentity,
)


@login_required
def cart_detail(request):
    """Render the authenticated user's cart summary."""
    return render(
        request,
        "cart/cart_detail.html",
        {"cart_summary": get_cart_summary(owner=request.user)},
    )


def cart_write_login_required(view_func):
    """Require login for a cart view, using the cart detail as the return URL."""

    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('users:login')}?next={reverse('cart:detail')}")
        return view_func(request, *args, **kwargs)

    return wrapped


@require_POST
@cart_write_login_required
def add_item(request):
    """Add an available offer to the authenticated user's cart via POST.

    Return 400 for an invalid offer ID and raise Http404 for a missing or
    unavailable offer. Redirect to the cart with a message indicating
    whether the item was added or already existed.
    """
    try:
        offer_id = int(request.POST.get("offer_id"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("offer_id no válido.")

    try:
        _, created = add_offer_to_cart(
            owner=request.user,
            offer_id=offer_id,
        )
    except OfferNotAvailable:
        raise Http404 from None
    except (LicenseAlreadyOwned, UnresolvedLicenseIdentity) as error:
        return HttpResponse(str(error), status=409)

    if created:
        messages.success(request, "Oferta añadida al carrito.")
    else:
        messages.info(request, "La oferta ya estaba en tu carrito.")
    return redirect("cart:detail")


@require_POST
@cart_write_login_required
def remove_item(request, item_id):
    """Remove an item from the authenticated user's cart via POST.

    Raise Http404 if no matching item exists in the user's cart.
    Redirect to the cart after removal.
    """
    try:
        remove_cart_item(owner=request.user, item_id=item_id)
    except CartItemNotFound:
        raise Http404 from None
    return redirect("cart:detail")
