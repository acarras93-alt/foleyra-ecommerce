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


def get_available_offers() -> QuerySet[ProductLicenseOffer]:
    return ProductLicenseOffer.objects.filter(
        is_active=True,
        product__is_active=True,
        product__category__is_active=True,
        license_type__is_active=True,
    )


def is_offer_available(offer: ProductLicenseOffer) -> bool:
    return (
        offer.is_active
        and offer.product.is_active
        and offer.product.category.is_active
        and offer.license_type.is_active
    )


def get_available_products(
    search_query: str = "",
    category_slug: str = "",
    license_slug: str = "",
    ordering: str = "",
) -> QuerySet[Product]:
    available_offers = get_available_offers()
    products = (
        Product.objects.filter(pk__in=available_offers.values("product_id"))
        .annotate(
            minimum_price=Min(
                "license_offers__price",
                filter=Q(license_offers__in=available_offers),
            )
        )
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "license_offers",
                queryset=available_offers.select_related("license_type"),
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
