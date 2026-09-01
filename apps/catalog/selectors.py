from django.db.models import Min, Prefetch, Q, QuerySet

from apps.catalog.models import Product, ProductLicenseOffer


def get_available_products(search_query: str = "") -> QuerySet[Product]:
    products = (
        Product.objects.filter(
            is_active=True,
            category__is_active=True,
            license_offers__is_active=True,
            license_offers__license_type__is_active=True,
        )
        .annotate(
            minimum_price=Min(
                "license_offers__price",
                filter=Q(
                    license_offers__is_active=True,
                    license_offers__license_type__is_active=True,
                ),
            )
        )
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "license_offers",
                queryset=ProductLicenseOffer.objects.filter(
                    is_active=True,
                    license_type__is_active=True,
                ).select_related("license_type"),
            )
        )
    )
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(summary__icontains=search_query)
            | Q(description__icontains=search_query)
        )
    return products.distinct().order_by("name", "pk")
