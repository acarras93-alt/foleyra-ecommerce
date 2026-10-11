from django.db import IntegrityError, transaction

from apps.cart.models import Cart, CartItem
from apps.catalog.models import ProductLicenseOffer
from apps.catalog.selectors import get_available_offers


class OfferNotAvailable(Exception):
    """Signal that an offer is missing or unavailable."""


class CartItemNotFound(Exception):
    """Signal that no matching item exists in the owner's cart."""


@transaction.atomic
def add_offer_to_cart(*, owner, offer_id: int) -> tuple[CartItem, bool]:
    """Add an available offer to the owner's cart, creating the cart if needed.

    Return the item and whether it was created. Reuse an existing item
    for the same offer.

    Raise OfferNotAvailable if the offer is missing or unavailable.
    """
    try:
        offer = get_available_offers().get(pk=offer_id)
    except ProductLicenseOffer.DoesNotExist:
        raise OfferNotAvailable from None

    cart, _ = Cart.objects.get_or_create(owner=owner)
    cart = Cart.objects.select_for_update().get(pk=cart.pk)
    try:
        with transaction.atomic():
            return CartItem.objects.get_or_create(cart=cart, offer=offer)
    except IntegrityError:
        return CartItem.objects.get(cart=cart, offer=offer), False


@transaction.atomic
def remove_cart_item(*, owner, item_id: int) -> None:
    """Delete an item from the owner's cart.

    Raise CartItemNotFound if the owner has no cart or the requested item
    does not belong to that cart.
    """
    try:
        cart = Cart.objects.select_for_update().get(owner=owner)
        item = CartItem.objects.get(pk=item_id, cart=cart)
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        raise CartItemNotFound from None
    item.delete()
