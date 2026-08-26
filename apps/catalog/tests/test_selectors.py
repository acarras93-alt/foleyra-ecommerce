from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer
from apps.catalog.selectors import get_available_products


def _create_available_products(category, license_type, start_number, amount):
    for number in range(start_number, start_number + amount):
        product = Product.objects.create(
            category=category,
            name=f"Producto {number:02d}",
            slug=f"producto-{number:02d}",
            sku=f"AMB-{number:03d}",
            summary="Ambiente ficticio de ciudad durante la noche.",
            description="Grabación preparada para una producción audiovisual.",
            duration_ms=18_500,
            audio_format="wav",
            sample_rate_hz=48_000,
            bit_depth=24,
        )
        ProductLicenseOffer.objects.create(
            product=product,
            license_type=license_type,
            price=Decimal("12.90"),
        )


def _load_available_products_and_relations():
    with CaptureQueriesContext(connection) as queries:
        products = list(get_available_products())
        for product in products:
            assert product.category.is_active
            assert all(offer.is_active for offer in product.license_offers.all())

    return products, len(queries)


@pytest.mark.django_db
def test_available_product_relations_use_a_constant_number_of_queries():
    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )
    _create_available_products(category, license_type, start_number=1, amount=1)

    one_product, one_product_query_count = _load_available_products_and_relations()

    _create_available_products(category, license_type, start_number=2, amount=11)

    twelve_products, twelve_product_query_count = (
        _load_available_products_and_relations()
    )

    assert len(one_product) == 1
    assert len(twelve_products) == 12
    assert one_product_query_count == twelve_product_query_count, (
        "The number of queries increased from "
        f"{one_product_query_count} to {twelve_product_query_count}."
    )
    assert twelve_product_query_count <= 3
