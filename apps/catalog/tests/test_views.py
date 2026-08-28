from decimal import Decimal
from pathlib import Path

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


@pytest.mark.django_db
def test_catalog_displays_the_minimum_price_for_multiple_active_offers(client):
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
    commercial_license_type = LicenseType.objects.create(
        name="Publicidad comercial",
        slug="publicidad-comercial",
        usage_scope="Una campaña publicitaria",
        summary="Uso en una campaña de publicidad comercial.",
        terms_version="1.0",
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=commercial_license_type,
        price=Decimal("29.90"),
    )

    response = client.get("/catalog/")
    content = response.content.decode()

    assert response.status_code == 200
    assert "Desde 12.90 EUR" in content
    assert "Desde 29.90 EUR" not in content


@pytest.mark.django_db
def test_product_detail_displays_technical_metadata_and_active_license_offer(client):
    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
        is_active=True,
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
        preview_file="previews/nocturnos-urbanos.mp3",
        is_active=True,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
        is_active=True,
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
        is_active=True,
    )

    response = client.get("/catalog/nocturnos-urbanos/")
    content = response.content.decode()

    assert response.status_code == 200
    for public_value in (
        product.name,
        category.name,
        product.description,
        "18500 ms",
        "WAV",
        "48000 Hz",
        "24 bits",
        license_type.name,
        license_type.usage_scope,
        license_type.summary,
        "12.90 EUR",
    ):
        assert public_value in content


@pytest.mark.django_db
def test_product_detail_returns_404_for_an_inactive_product(client):
    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
        is_active=True,
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
        preview_file="previews/nocturnos-urbanos-archivados.mp3",
        is_active=False,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
        is_active=True,
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
        is_active=True,
    )

    response = client.get("/catalog/nocturnos-urbanos-archivados/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_product_detail_returns_404_for_an_unknown_slug(client):
    response = client.get("/catalog/slug-inexistente/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_product_detail_returns_404_for_an_inactive_category(client):
    category = Category.objects.create(
        name="Ambientes archivados",
        slug="ambientes-archivados",
        is_active=False,
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos de categoria archivada",
        slug="nocturnos-urbanos-categoria-archivada",
        sku="AMB-003",
        summary="Ambiente ficticio de ciudad durante la noche.",
        description="Grabación preparada para una producción audiovisual.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        preview_file="previews/nocturnos-urbanos-categoria-archivada.mp3",
        is_active=True,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
        is_active=True,
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
        is_active=True,
    )

    response = client.get("/catalog/nocturnos-urbanos-categoria-archivada/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_product_detail_returns_404_without_an_active_license_offer(client):
    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
        is_active=True,
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos sin oferta activa",
        slug="nocturnos-urbanos-sin-oferta-activa",
        sku="AMB-004",
        summary="Ambiente ficticio de ciudad durante la noche.",
        description="Grabación preparada para una producción audiovisual.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        preview_file="previews/nocturnos-urbanos-sin-oferta-activa.mp3",
        is_active=True,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
        is_active=True,
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
        is_active=False,
    )

    response = client.get("/catalog/nocturnos-urbanos-sin-oferta-activa/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_product_detail_excludes_an_inactive_license_offer(client):
    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
        is_active=True,
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos",
        slug="nocturnos-urbanos",
        sku="AMB-005",
        summary="Ambiente ficticio de ciudad durante la noche.",
        description="Grabación preparada para una producción audiovisual.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        preview_file="previews/nocturnos-urbanos.mp3",
        is_active=True,
    )
    active_license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
        is_active=True,
    )
    inactive_license_type = LicenseType.objects.create(
        name="Publicidad comercial",
        slug="publicidad-comercial",
        usage_scope="Una campaña publicitaria",
        summary="Uso en una campaña de publicidad comercial.",
        terms_version="1.0",
        is_active=True,
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=active_license_type,
        price=Decimal("12.90"),
        is_active=True,
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=inactive_license_type,
        price=Decimal("29.90"),
        is_active=False,
    )

    response = client.get("/catalog/nocturnos-urbanos/")
    content = response.content.decode()

    assert response.status_code == 200
    assert active_license_type.name in content
    assert inactive_license_type.name not in content


@pytest.mark.django_db
def test_product_detail_displays_a_message_when_preview_is_unavailable(client):
    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
        is_active=True,
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos sin preview",
        slug="nocturnos-urbanos-sin-preview",
        sku="AMB-006",
        summary="Ambiente ficticio de ciudad durante la noche.",
        description="Grabacion preparada para una produccion audiovisual.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        preview_file="",
        is_active=True,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
        is_active=True,
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
        is_active=True,
    )

    response = client.get("/catalog/nocturnos-urbanos-sin-preview/")

    assert response.status_code == 200
    assert "Preview no disponible." in response.content.decode()


@pytest.mark.django_db
def test_product_detail_without_preview_never_exposes_the_private_master(client):
    master_name = "masters/identifiable-private-master.wav"
    category = Category.objects.create(
        name="Ambientes con maestro privado",
        slug="ambientes-con-maestro-privado",
        is_active=True,
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos sin preview con maestro privado",
        slug="nocturnos-urbanos-sin-preview-con-maestro-privado",
        sku="AMB-007",
        summary="Ambiente ficticio con preview ausente.",
        description="Grabación preparada con un maestro privado identificable.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        preview_file="",
        master_file=master_name,
        is_active=True,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales con maestro privado",
        slug="youtube-redes-sociales-con-maestro-privado",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
        is_active=True,
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
        is_active=True,
    )

    product.refresh_from_db()

    assert product.master_file.name == master_name
    assert (
        Path(product.preview_file.storage.location).resolve()
        != Path(product.master_file.storage.location).resolve()
    )
    with pytest.raises(NotImplementedError) as error:
        _ = product.master_file.url
    assert master_name not in str(error.value)
    assert Path(master_name).name not in str(error.value)

    response = client.get("/catalog/nocturnos-urbanos-sin-preview-con-maestro-privado/")
    content = response.content.decode()

    assert response.status_code == 200
    assert "Preview no disponible." in content
    assert master_name not in content
    assert Path(master_name).name not in content
