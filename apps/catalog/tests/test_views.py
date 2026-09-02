import html
import importlib
import re
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs

import pytest
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import clear_url_caches

from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer
from config import urls as project_urls


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
def test_catalog_pagination_link_preserves_only_search_filters_and_ordering(client):
    _create_available_products(13)
    query_params = {
        "q": "ciudad",
        "category": "ambientes",
        "license": "youtube-redes-sociales",
        "ordering": "name",
        "utm_source": "newsletter",
    }

    first_page_response = client.get("/catalog/", query_params)
    second_page_response = client.get("/catalog/", {**query_params, "page": "2"})

    assert first_page_response.status_code == 200
    assert second_page_response.status_code == 200
    first_page_content = first_page_response.content.decode()
    second_page_content = second_page_response.content.decode()

    next_link_match = re.search(r'href="([^"]+)">Siguiente', first_page_content)
    assert next_link_match is not None
    next_query = parse_qs(html.unescape(next_link_match.group(1)).lstrip("?"))

    assert next_query == {
        "q": ["ciudad"],
        "category": ["ambientes"],
        "license": ["youtube-redes-sociales"],
        "ordering": ["name"],
        "page": ["2"],
    }

    previous_link_match = re.search(r'href="([^"]+)">Anterior', second_page_content)
    assert previous_link_match is not None
    previous_query = parse_qs(html.unescape(previous_link_match.group(1)).lstrip("?"))

    assert previous_query == {
        "q": ["ciudad"],
        "category": ["ambientes"],
        "license": ["youtube-redes-sociales"],
        "ordering": ["name"],
        "page": ["1"],
    }


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
def test_catalog_searches_available_products_by_normalized_text_case_insensitively(
    client,
):
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
    product_data = (
        (
            "CITY NIGHT en el puerto",
            "Puerto al anochecer.",
            "Grabación de ambiente marítimo.",
            True,
        ),
        (
            "Tráfico distante",
            "Ambiente de CITY NIGHT con tráfico.",
            "Grabación de una avenida.",
            True,
        ),
        (
            "Pasos sobre asfalto",
            "Pasos nocturnos.",
            "Grabación durante una CITY NIGHT lluviosa.",
            True,
        ),
        (
            "Amanecer rural",
            "Ambiente de campo.",
            "Grabación de aves al amanecer.",
            True,
        ),
        (
            "CITY NIGHT archivada",
            "Ambiente retirado.",
            "Grabación que ya no está disponible.",
            False,
        ),
    )
    products = []
    for number, (name, summary, description, is_active) in enumerate(
        product_data,
        start=1,
    ):
        product = Product.objects.create(
            category=category,
            name=name,
            slug=f"producto-busqueda-{number}",
            sku=f"SEARCH-{number}",
            summary=summary,
            description=description,
            duration_ms=18_500,
            audio_format="wav",
            sample_rate_hz=48_000,
            bit_depth=24,
            is_active=is_active,
        )
        ProductLicenseOffer.objects.create(
            product=product,
            license_type=license_type,
            price=Decimal("12.90"),
        )
        products.append(product)

    response = client.get("/catalog/", {"q": "  city   night  "})
    content = response.content.decode()

    assert response.status_code == 200
    for product in products[:3]:
        assert product.name in content
    for product in products[3:]:
        assert product.name not in content


@pytest.mark.django_db
def test_catalog_returns_400_for_a_normalized_search_query_longer_than_100_characters(
    client,
):
    response = client.get("/catalog/", {"q": "a" * 101})

    assert response.status_code == 400
    assert "q" in response.content.decode()


@pytest.mark.django_db
def test_catalog_filters_available_products_by_category_and_license_slug(client):
    matching_category = Category.objects.create(name="Ambientes", slug="ambientes")
    other_category = Category.objects.create(name="Efectos", slug="efectos")
    matching_license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )
    other_license_type = LicenseType.objects.create(
        name="Publicidad comercial",
        slug="publicidad-comercial",
        usage_scope="Una campaña publicitaria",
        summary="Uso en una campaña de publicidad comercial.",
        terms_version="1.0",
    )

    matching_product = Product.objects.create(
        category=matching_category,
        name="Puerto al anochecer",
        slug="puerto-al-anochecer",
        sku="AMB-101",
        summary="Ambiente de puerto durante la noche.",
        description="Grabación de ambiente marítimo.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    ProductLicenseOffer.objects.create(
        product=matching_product,
        license_type=matching_license_type,
        price=Decimal("12.90"),
    )

    wrong_license_product = Product.objects.create(
        category=matching_category,
        name="Tráfico distante",
        slug="trafico-distante",
        sku="AMB-102",
        summary="Ambiente de tráfico urbano.",
        description="Grabación de una avenida.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    ProductLicenseOffer.objects.create(
        product=wrong_license_product,
        license_type=other_license_type,
        price=Decimal("29.90"),
    )

    wrong_category_product = Product.objects.create(
        category=other_category,
        name="Impacto metálico",
        slug="impacto-metalico",
        sku="EFE-101",
        summary="Efecto de impacto metálico.",
        description="Grabación de un golpe sobre metal.",
        duration_ms=1_200,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    ProductLicenseOffer.objects.create(
        product=wrong_category_product,
        license_type=matching_license_type,
        price=Decimal("9.90"),
    )

    response = client.get(
        "/catalog/",
        {"category": matching_category.slug, "license": matching_license_type.slug},
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert matching_product.name in content
    assert wrong_license_product.name not in content
    assert wrong_category_product.name not in content


@pytest.mark.django_db
def test_catalog_orders_available_products_by_minimum_price_with_stable_tiebreak(
    client,
):
    category = Category.objects.create(name="Ambientes", slug="ambientes")
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )

    def _create_product_with_price(name, slug, sku, price):
        product = Product.objects.create(
            category=category,
            name=name,
            slug=slug,
            sku=sku,
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
            price=Decimal(price),
        )
        return product

    low_first = _create_product_with_price(
        "Alfa baja uno", "alfa-baja-uno", "PRC-001", "10.00"
    )
    low_second = _create_product_with_price(
        "Beta baja dos", "beta-baja-dos", "PRC-002", "10.00"
    )
    mid = _create_product_with_price("Gamma media", "gamma-media", "PRC-003", "20.00")
    high = _create_product_with_price("Zeta alta", "zeta-alta", "PRC-004", "30.00")

    ascending_content = client.get("/catalog/", {"ordering": "price"}).content.decode()
    descending_content = client.get(
        "/catalog/", {"ordering": "-price"}
    ).content.decode()

    ascending_positions = [
        ascending_content.index(product.name)
        for product in (low_first, low_second, mid, high)
    ]
    descending_positions = [
        descending_content.index(product.name)
        for product in (high, mid, low_first, low_second)
    ]

    assert ascending_positions == sorted(ascending_positions)
    assert descending_positions == sorted(descending_positions)


@pytest.mark.django_db
def test_catalog_orders_available_products_by_name_in_descending_order(client):
    category = Category.objects.create(name="Ambientes", slug="ambientes")
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )

    def _create_product(name, slug, sku):
        product = Product.objects.create(
            category=category,
            name=name,
            slug=slug,
            sku=sku,
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
        return product

    first_alphabetically = _create_product("Alfa baja", "alfa-baja", "PRC-101")
    last_alphabetically = _create_product("Zeta alta", "zeta-alta", "PRC-102")

    content = client.get("/catalog/", {"ordering": "-name"}).content.decode()

    assert content.index(last_alphabetically.name) < content.index(
        first_alphabetically.name
    )


@pytest.mark.django_db
def test_catalog_returns_400_for_an_unrecognized_ordering_value(client):
    response = client.get("/catalog/", {"ordering": "unknown"})

    assert response.status_code == 400
    assert "ordering" in response.content.decode()


@pytest.mark.django_db
def test_catalog_returns_400_for_an_unrecognized_category_slug(client):
    response = client.get("/catalog/", {"category": "categoria-inexistente"})

    assert response.status_code == 400
    assert "category" in response.content.decode()


@pytest.mark.django_db
def test_catalog_returns_400_for_an_unrecognized_license_slug(client):
    response = client.get("/catalog/", {"license": "licencia-inexistente"})

    assert response.status_code == 400
    assert "license" in response.content.decode()


@pytest.mark.django_db
def test_catalog_returns_400_instead_of_404_when_an_invalid_category_and_an_invalid_page_are_combined(
    client,
):
    response = client.get(
        "/catalog/", {"category": "categoria-inexistente", "page": "999"}
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_catalog_renders_category_and_license_selects_with_active_options_and_recognized_value(
    client,
):
    matching_category = Category.objects.create(name="Ambientes", slug="ambientes")
    other_category = Category.objects.create(name="Efectos", slug="efectos")
    Category.objects.create(name="Retirada", slug="retirada", is_active=False)
    matching_license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )
    other_license_type = LicenseType.objects.create(
        name="Publicidad comercial",
        slug="publicidad-comercial",
        usage_scope="Una campaña publicitaria",
        summary="Uso en una campaña de publicidad comercial.",
        terms_version="1.0",
    )
    LicenseType.objects.create(
        name="Retirada",
        slug="retirada-licencia",
        usage_scope="Uso retirado",
        summary="Tipo de licencia retirado.",
        terms_version="1.0",
        is_active=False,
    )

    response = client.get(
        "/catalog/",
        {"category": matching_category.slug, "license": matching_license_type.slug},
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert '<select name="category">' in content
    assert '<select name="license">' in content
    assert content.count('<option value="">Todas</option>') == 2

    assert (
        f'<option value="{matching_category.slug}" selected>{matching_category.name}</option>'
        in content
    )
    assert (
        f'<option value="{other_category.slug}">{other_category.name}</option>'
        in content
    )
    assert "retirada" not in content

    assert (
        f'<option value="{matching_license_type.slug}" selected>'
        f"{matching_license_type.name}</option>" in content
    )
    assert (
        f'<option value="{other_license_type.slug}">{other_license_type.name}</option>'
        in content
    )
    assert "retirada-licencia" not in content


@pytest.mark.django_db
def test_catalog_shows_message_and_keeps_all_recognized_controls_visible_when_query_has_no_matches(
    client,
):
    _create_available_products(1)

    response = client.get(
        "/catalog/",
        {
            "q": "cadena-sin-coincidencias",
            "category": "ambientes",
            "license": "youtube-redes-sociales",
            "ordering": "price",
        },
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert "No hay productos disponibles en este momento." in content
    assert '<option value="ambientes" selected>' in content
    assert '<option value="youtube-redes-sociales" selected>' in content
    assert '<input type="text" name="q" value="cadena-sin-coincidencias">' in content
    assert '<select name="ordering">' in content
    assert 'value="price" selected' in content


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


@pytest.mark.django_db
def test_product_detail_context_excludes_the_private_master(client):
    master_name = "masters/context-identifiable-private-master.wav"
    category = Category.objects.create(
        name="Ambientes con contexto público",
        slug="ambientes-con-contexto-publico",
        is_active=True,
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos con contexto público",
        slug="nocturnos-urbanos-con-contexto-publico",
        sku="AMB-008",
        summary="Ambiente ficticio con contexto público.",
        description="Grabación preparada con un maestro privado identificable.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        preview_file="previews/context-public-preview.mp3",
        master_file=master_name,
        is_active=True,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales con contexto público",
        slug="youtube-redes-sociales-con-contexto-publico",
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

    response = client.get("/catalog/nocturnos-urbanos-con-contexto-publico/")
    public_context = {}
    for context in response.context:
        public_context.update(context.flatten())

    assert response.status_code == 200
    assert all(not hasattr(value, "master_file") for value in public_context.values())
    assert master_name not in str(public_context)
    assert Path(master_name).name not in str(public_context)
    assert str(product.master_file.storage.location) not in str(public_context)


@pytest.mark.django_db
def test_anonymous_visitor_can_browse_the_public_product_flow_safely(client):
    master_name = "masters/rf02-acceptance-private-master.wav"
    category = Category.objects.create(
        name="Ambientes RF-02",
        slug="ambientes-rf02",
        is_active=True,
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos RF-02",
        slug="nocturnos-urbanos-rf02",
        sku="AMB-RF02",
        summary="Ambiente ficticio para la aceptación de RF-02.",
        description="Grabación preparada para el flujo público de RF-02.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        preview_file="previews/rf02-public-preview.mp3",
        master_file=master_name,
        is_active=True,
    )
    active_license_type = LicenseType.objects.create(
        name="YouTube y redes sociales RF-02",
        slug="youtube-redes-sociales-rf02",
        usage_scope="Un canal por plataforma",
        summary="Uso activo para el flujo público de RF-02.",
        terms_version="1.0",
        is_active=True,
    )
    inactive_license_type = LicenseType.objects.create(
        name="Publicidad inactiva RF-02",
        slug="publicidad-inactiva-rf02",
        usage_scope="Una campaña publicitaria",
        summary="Oferta inactiva que no debe ser pública.",
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

    catalog_response = client.get("/catalog/")
    catalog_content = catalog_response.content.decode()

    assert catalog_response.status_code == 200
    assert product.name in catalog_content

    detail_response = client.get(f"/catalog/{product.slug}/")
    detail_content = detail_response.content.decode()
    public_context = {}
    for context in detail_response.context:
        public_context.update(context.flatten())

    assert detail_response.status_code == 200
    for public_value in (
        product.name,
        category.name,
        product.description,
        "18500 ms",
        "WAV",
        "48000 Hz",
        "24 bits",
        active_license_type.name,
        active_license_type.usage_scope,
        active_license_type.summary,
        "12.90 EUR",
    ):
        assert public_value in detail_content
    assert inactive_license_type.name not in detail_content
    assert product.preview_file.url in detail_content
    assert "Preview no disponible." not in detail_content
    assert all(not hasattr(value, "master_file") for value in public_context.values())
    for private_value in (
        master_name,
        Path(master_name).name,
        str(product.master_file.storage.location),
    ):
        assert private_value not in detail_content
        assert private_value not in str(public_context)


def test_anonymous_visitor_receives_the_public_preview_file(
    client,
    monkeypatch,
    tmp_path,
):
    preview_bytes = b"ID3\x04\x00\x00fictional-preview-bytes"
    preview_storage = Product._meta.get_field("preview_file").storage
    monkeypatch.setattr(preview_storage, "_location", tmp_path)
    preview_storage.__dict__.pop("base_location", None)
    preview_storage.__dict__.pop("location", None)

    try:
        with override_settings(
            DEBUG=True,
            MEDIA_ROOT=tmp_path,
            MEDIA_URL="/media/",
        ):
            clear_url_caches()
            importlib.reload(project_urls)
            product = Product()
            product.preview_file.save(
                "ca-rf02-02-public-preview.mp3",
                ContentFile(preview_bytes),
                save=False,
            )

            try:
                response = client.get(product.preview_file.url)

                assert response.status_code == 200
                assert b"".join(response.streaming_content) == preview_bytes
            finally:
                product.preview_file.delete(save=False)
    finally:
        clear_url_caches()
        importlib.reload(project_urls)
