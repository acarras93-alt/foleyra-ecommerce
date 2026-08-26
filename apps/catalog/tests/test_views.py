from decimal import Decimal

import pytest

from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer


@pytest.mark.django_db
def test_catalog_displays_an_active_product_with_an_active_category_and_license_offer(
    client,
):
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
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )

    response = client.get("/catalog/")

    assert response.status_code == 200
    assert product.name in response.content.decode()


@pytest.mark.django_db
def test_catalog_excludes_an_inactive_product_with_an_active_category_and_license_offer(
    client,
):
    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos archivados",
        slug="nocturnos-urbanos-archivados",
        sku="AMB-002",
        summary="Ambiente ficticio retirado de ciudad durante la noche.",
        description="Grabación retirada de una producción audiovisual.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        is_active=False,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )

    response = client.get("/catalog/")

    assert response.status_code == 200
    assert product.name not in response.content.decode()


@pytest.mark.django_db
def test_catalog_displays_a_message_when_no_products_are_available(client):
    response = client.get("/catalog/")

    assert response.status_code == 200
    assert "No hay productos disponibles en este momento." in response.content.decode()
