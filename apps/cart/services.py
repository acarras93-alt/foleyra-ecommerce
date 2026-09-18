from django.db import IntegrityError, transaction

from apps.cart.models import Cart, CartItem
from apps.catalog.models import ProductLicenseOffer
from apps.catalog.selectors import get_available_offers


class OfferNotAvailable(Exception):
    pass


class CartItemNotFound(Exception):
    pass


@transaction.atomic
def add_offer_to_cart(*, owner, offer_id: int) -> tuple[CartItem, bool]:
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
    try:
        cart = Cart.objects.select_for_update().get(owner=owner)
        item = CartItem.objects.get(pk=item_id, cart=cart)
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        raise CartItemNotFound from None
    item.delete()
