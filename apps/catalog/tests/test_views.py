from decimal import Decimal

import pytest

from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer


def _create_available_products(number_of_products):
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
    for number in range(1, number_of_products + 1):
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


@pytest.mark.django_db
def test_catalog_displays_the_second_page_of_available_products(client):
    _create_available_products(13)

    response = client.get("/catalog/?page=2")
    content = response.content.decode()

    assert response.status_code == 200
    assert "Producto 13" in content
    for number in range(1, 13):
        assert f"Producto {number:02d}" not in content


@pytest.mark.django_db
def test_catalog_displays_navigation_links_only_for_existing_pages(client):
    _create_available_products(13)

    first_page = client.get("/catalog/?page=1")
    second_page = client.get("/catalog/?page=2")

    assert first_page.status_code == 200
    assert 'href="?page=2"' in first_page.content.decode()
    assert 'href="?page=1"' not in first_page.content.decode()
    assert second_page.status_code == 200
    assert 'href="?page=1"' in second_page.content.decode()
    assert 'href="?page=2"' not in second_page.content.decode()


@pytest.mark.django_db
def test_catalog_returns_404_for_a_page_beyond_the_available_pages(client):
    _create_available_products(13)

    response = client.get("/catalog/?page=3")

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("page", ["abc", "0"])
def test_catalog_returns_404_for_an_invalid_page(client, page):
    response = client.get("/catalog/", {"page": page})

    assert response.status_code == 404
