from django.db.models import Min, Prefetch, Q, QuerySet

from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer

ORDERING_OPTIONS = {
    "name": ("name", "pk"),
    "-name": ("-name", "pk"),
    "price": ("minimum_price", "pk"),
    "-price": ("-minimum_price", "pk"),
}


def get_active_categories() -> QuerySet[Category]:
    return Category.objects.filter(is_active=True)


def get_active_license_types() -> QuerySet[LicenseType]:
    return LicenseType.objects.filter(is_active=True)


def get_available_products(
    search_query: str = "",
    category_slug: str = "",
    license_slug: str = "",
    ordering: str = "",
) -> QuerySet[Product]:
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
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if license_slug:
        products = products.filter(license_offers__license_type__slug=license_slug)
    return products.distinct().order_by(*ORDERING_OPTIONS.get(ordering, ("name", "pk")))
