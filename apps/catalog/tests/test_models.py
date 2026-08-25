from decimal import Decimal

import pytest

from apps.catalog.models import (
    Category,
    LicenseType,
    Product,
    ProductLicenseOffer,
)


@pytest.mark.django_db
def test_product_license_offer_defines_a_unitary_purchase_option():
    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos",
        slug="nocturnos-urbanos",
        sku="AMB-001",
        summary="Ambiente ficticio de ciudad durante la noche.",
        description="Grabación preparada para una producción audiovisual.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    creator = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )
    cinema = LicenseType.objects.create(
        name="Producción cinematográfica",
        slug="produccion-cinematografica",
        usage_scope="Una producción audiovisual",
        summary="Uso sincronizado en una producción cinematográfica.",
        terms_version="1.0",
    )

    creator_offer = ProductLicenseOffer.objects.create(
        product=product,
        license_type=creator,
        price=Decimal("12.90"),
    )
    cinema_offer = ProductLicenseOffer.objects.create(
        product=product,
        license_type=cinema,
        price=Decimal("49.90"),
    )

    assert creator_offer.product == product
    assert creator_offer.license_type == creator
    assert cinema_offer.product == product
    assert cinema_offer.license_type == cinema
    assert list(
        ProductLicenseOffer.objects.filter(product=product)
        .order_by("price")
        .values_list("price", flat=True)
    ) == [Decimal("12.90"), Decimal("49.90")]
