from django.db.models import Min, Q, QuerySet

from apps.catalog.models import Product


def get_available_products() -> QuerySet[Product]:
    return (
        Product.objects.filter(
            is_active=True,
            category__is_active=True,
            license_offers__is_active=True,
        )
        .annotate(
            minimum_price=Min(
                "license_offers__price",
                filter=Q(license_offers__is_active=True),
            )
        )
        .distinct()
        .order_by("name", "pk")
    )
