from decimal import Decimal

from django.db import transaction

from apps.cart.models import Cart, CartItem
from apps.catalog.selectors import is_offer_available
from apps.orders.models import Order, OrderItem


class EmptyCart(Exception):
    pass


class OfferNotAvailable(Exception):
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
                product_sku=item.offer.product.sku,
                product_name=item.offer.product.name,
                license_name=item.offer.license_type.name,
                terms_version=item.offer.license_type.terms_version,
                price=item.offer.price,
                currency=item.offer.currency,
            )
            for item in cart_items
        ]
    )
    CartItem.objects.filter(cart=cart).delete()
    return order
