from dataclasses import dataclass
from decimal import Decimal

from apps.cart.models import CartItem
from apps.catalog.selectors import is_offer_available


@dataclass(frozen=True)
class CartSummaryItem:
    item_id: int
    offer_id: int
    product_name: str
    product_slug: str
    license_name: str
    usage_scope: str
    terms_version: str
    price: Decimal
    currency: str
    is_available: bool


@dataclass(frozen=True)
class CartSummary:
    items: tuple[CartSummaryItem, ...]
    total: Decimal


def get_cart_summary(*, owner) -> CartSummary:
    cart_items = (
        CartItem.objects.filter(cart__owner=owner)
        .select_related(
            "offer__product__category",
            "offer__license_type",
        )
        .order_by("pk")
    )
    total = Decimal("0.00")
    summary_items = []
    for item in cart_items:
        offer = item.offer
        available = is_offer_available(offer)
        summary_items.append(
            CartSummaryItem(
                item_id=item.pk,
                offer_id=offer.pk,
                product_name=offer.product.name,
                product_slug=offer.product.slug,
                license_name=offer.license_type.name,
                usage_scope=offer.license_type.usage_scope,
                terms_version=offer.license_type.terms_version,
                price=offer.price,
                currency=offer.currency,
                is_available=available,
            )
        )
        if available:
            total += offer.price
    return CartSummary(items=tuple(summary_items), total=total)
