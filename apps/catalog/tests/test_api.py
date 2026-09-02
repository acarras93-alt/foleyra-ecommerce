from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer


def _create_available_api_products(category, license_type, start_number, amount):
    for number in range(start_number, start_number + amount):
        product = Product.objects.create(
            category=category,
            name=f"Producto de rendimiento API {number:02d}",
            slug=f"producto-rendimiento-api-{number:02d}",
            sku=f"PERF-API-{number:03d}",
            summary="Ambiente ficticio para medir consultas.",
            description="Grabación preparada para medir consultas de la API.",
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


def _request_public_product_page_with_query_count(client):
    with CaptureQueriesContext(connection) as queries:
        response = client.get("/api/v1/catalog/products/")
        response_data = response.json()

    assert response.status_code == 200
    assert all(
        product["category"]["slug"]
        and product["licenses"][0]["slug"]
        and product["minimum_price"]
        for product in response_data["results"]
    )
    return response_data, len(queries)


@pytest.mark.django_db
def test_public_product_api_serialization_uses_a_constant_number_of_queries(client):
    category = Category.objects.create(
        name="Ambientes de rendimiento API",
        slug="ambientes-rendimiento-api",
    )
    license_type = LicenseType.objects.create(
        name="YouTube de rendimiento API",
        slug="youtube-rendimiento-api",
        usage_scope="Un canal por plataforma",
        summary="Uso para medir consultas de la API.",
        terms_version="1.0",
    )
    _create_available_api_products(
        category,
        license_type,
        start_number=1,
        amount=1,
    )

    one_product_page, one_product_query_count = (
        _request_public_product_page_with_query_count(client)
    )

    _create_available_api_products(
        category,
        license_type,
        start_number=2,
        amount=11,
    )

    twelve_product_page, twelve_product_query_count = (
        _request_public_product_page_with_query_count(client)
    )

    assert len(one_product_page["results"]) == 1
    assert len(twelve_product_page["results"]) == 12
    assert one_product_query_count == twelve_product_query_count, (
        "The number of queries increased from "
        f"{one_product_query_count} to {twelve_product_query_count}."
    )
    assert twelve_product_query_count <= 3


@pytest.mark.django_db
def test_public_product_api_returns_an_empty_page_for_a_valid_query(client):
    response = client.get("/api/v1/catalog/products/")

    assert response.status_code == 200
    assert response.json() == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }


@pytest.mark.django_db
def test_public_product_api_uses_canonical_relative_pagination_links(client):
    category = Category.objects.create(
        name="Ambientes de paginación API",
        slug="ambientes-paginacion-api",
    )
    license_type = LicenseType.objects.create(
        name="YouTube de paginación API",
        slug="youtube-paginacion-api",
        usage_scope="Un canal por plataforma",
        summary="Uso para comprobar enlaces de paginación.",
        terms_version="1.0",
    )
    _create_available_api_products(
        category,
        license_type,
        start_number=1,
        amount=13,
    )
    query_params = {
        "q": "  consultas  ",
        "category": category.slug,
        "license": license_type.slug,
        "ordering": "name",
        "utm_source": "newsletter",
    }

    first_page = client.get("/api/v1/catalog/products/", query_params)
    second_page = client.get(
        "/api/v1/catalog/products/",
        {**query_params, "page": "2"},
    )
    canonical_query = (
        "q=consultas&category=ambientes-paginacion-api&"
        "license=youtube-paginacion-api&ordering=name"
    )

    assert first_page.status_code == 200
    assert first_page.json()["next"] == (
        f"/api/v1/catalog/products/?{canonical_query}&page=2"
    )
    assert first_page.json()["previous"] is None
    assert second_page.status_code == 200
    assert second_page.json()["next"] is None
    assert second_page.json()["previous"] == (
        f"/api/v1/catalog/products/?{canonical_query}&page=1"
    )


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/catalog/products/",
        "/api/v1/catalog/products/no-existe/",
    ],
)
def test_authenticated_consumer_cannot_write_to_the_public_catalog(
    client, method, path
):
    user = get_user_model().objects.create_user(
        username="api-consumer",
        password="unused-password",
    )
    client.force_login(user)

    response = getattr(client, method)(path)

    assert response.status_code == 405
    assert response.json() == {"error": {"code": "method_not_allowed"}}


@pytest.mark.django_db
@pytest.mark.parametrize("ordering", ["name", "-name", "price", "-price"])
def test_public_product_api_matches_web_for_valid_query_parameters(client, ordering):
    matching_category = Category.objects.create(
        name="Ambientes API",
        slug="ambientes-api",
    )
    other_category = Category.objects.create(
        name="Efectos API",
        slug="efectos-api",
    )
    matching_license = LicenseType.objects.create(
        name="YouTube API",
        slug="youtube-api",
        usage_scope="Un canal por plataforma",
        summary="Uso para comprobar equivalencia.",
        terms_version="1.0",
    )
    other_license = LicenseType.objects.create(
        name="Publicidad API",
        slug="publicidad-api",
        usage_scope="Una campaña publicitaria",
        summary="Uso alternativo para comprobar filtros.",
        terms_version="1.0",
    )

    matching_product = Product.objects.create(
        category=matching_category,
        name="City Night API",
        slug="city-night-api",
        sku="API-001",
        summary="Ambiente nocturno.",
        description="Grabación de ciudad.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    ProductLicenseOffer.objects.create(
        product=matching_product,
        license_type=matching_license,
        price=Decimal("20.00"),
    )
    second_matching_product = Product.objects.create(
        category=matching_category,
        name="Amanecer API",
        slug="amanecer-api",
        sku="API-004",
        summary="City Night ambiente.",
        description="Grabación de ciudad.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    ProductLicenseOffer.objects.create(
        product=second_matching_product,
        license_type=matching_license,
        price=Decimal("10.00"),
    )
    third_matching_product = Product.objects.create(
        category=matching_category,
        name="Puerto API",
        slug="puerto-api",
        sku="API-006",
        summary="Ambiente nocturno.",
        description="Grabación de City Night.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    ProductLicenseOffer.objects.create(
        product=third_matching_product,
        license_type=matching_license,
        price=Decimal("30.00"),
    )
    non_matching_search_product = Product.objects.create(
        category=matching_category,
        name="Bosque API",
        slug="bosque-api",
        sku="API-005",
        summary="Ambiente al amanecer.",
        description="Grabación rural.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    ProductLicenseOffer.objects.create(
        product=non_matching_search_product,
        license_type=matching_license,
        price=Decimal("12.90"),
    )
    other_category_product = Product.objects.create(
        category=other_category,
        name="City Night efecto API",
        slug="city-night-efecto-api",
        sku="API-002",
        summary="Efecto nocturno.",
        description="Grabación de ciudad.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    ProductLicenseOffer.objects.create(
        product=other_category_product,
        license_type=matching_license,
        price=Decimal("12.90"),
    )
    other_license_product = Product.objects.create(
        category=matching_category,
        name="City Night publicidad API",
        slug="city-night-publicidad-api",
        sku="API-003",
        summary="Ambiente nocturno.",
        description="Grabación de ciudad.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    ProductLicenseOffer.objects.create(
        product=other_license_product,
        license_type=other_license,
        price=Decimal("12.90"),
    )
    query_params = {
        "q": "  city   night  ",
        "category": matching_category.slug,
        "license": matching_license.slug,
        "ordering": ordering,
    }

    web_response = client.get("/catalog/", query_params)
    api_response = client.get("/api/v1/catalog/products/", query_params)

    assert web_response.status_code == 200
    assert api_response.status_code == 200
    expected_slugs_by_ordering = {
        "name": [
            second_matching_product.slug,
            matching_product.slug,
            third_matching_product.slug,
        ],
        "-name": [
            third_matching_product.slug,
            matching_product.slug,
            second_matching_product.slug,
        ],
        "price": [
            second_matching_product.slug,
            matching_product.slug,
            third_matching_product.slug,
        ],
        "-price": [
            third_matching_product.slug,
            matching_product.slug,
            second_matching_product.slug,
        ],
    }
    expected_slugs = expected_slugs_by_ordering[ordering]
    assert [
        product.slug for product in web_response.context["products"]
    ] == expected_slugs
    assert [
        product["slug"] for product in api_response.json()["results"]
    ] == expected_slugs


@pytest.mark.django_db
def test_anonymous_consumer_receives_a_public_product_detail(client):
    category = Category.objects.create(
        name="Ambientes de detalle",
        slug="ambientes-detalle",
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos de detalle",
        slug="nocturnos-urbanos-detalle",
        sku="DETAIL-001",
        summary="Ambiente ficticio de ciudad durante la noche.",
        description="Grabación preparada para una producción audiovisual.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        preview_file="previews/nocturnos-urbanos-detalle.mp3",
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales de detalle",
        slug="youtube-redes-sociales-detalle",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )

    response = client.get(f"/api/v1/catalog/products/{product.slug}/")

    assert response.status_code == 200
    assert response.json() == {
        "name": product.name,
        "slug": product.slug,
        "summary": product.summary,
        "category": {"name": category.name, "slug": category.slug},
        "duration_ms": product.duration_ms,
        "audio_format": product.audio_format,
        "sample_rate_hz": product.sample_rate_hz,
        "bit_depth": product.bit_depth,
        "minimum_price": "12.90",
        "currency": "EUR",
        "description": product.description,
        "preview_url": "/media/previews/nocturnos-urbanos-detalle.mp3",
        "license_offers": [
            {
                "license": {
                    "name": license_type.name,
                    "slug": license_type.slug,
                    "usage_scope": license_type.usage_scope,
                    "summary": license_type.summary,
                },
                "price": "12.90",
                "currency": "EUR",
            }
        ],
        "detail_url": f"/api/v1/catalog/products/{product.slug}/",
    }


@pytest.mark.django_db
def test_public_product_detail_omits_unavailable_preview_and_license_offers(client):
    category = Category.objects.create(
        name="Ambientes sin preview API",
        slug="ambientes-sin-preview-api",
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos sin preview API",
        slug="nocturnos-urbanos-sin-preview-api",
        sku="DETAIL-002",
        summary="Ambiente ficticio sin preview.",
        description="Grabación preparada para comprobar ofertas públicas.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    active_license = LicenseType.objects.create(
        name="YouTube activo de detalle",
        slug="youtube-activo-detalle",
        usage_scope="Un canal por plataforma",
        summary="Uso público activo.",
        terms_version="1.0",
    )
    inactive_license = LicenseType.objects.create(
        name="Publicidad inactiva de detalle",
        slug="publicidad-inactiva-detalle",
        usage_scope="Una campaña publicitaria",
        summary="Uso que no debe exponerse.",
        terms_version="1.0",
    )
    lower_price_license = LicenseType.objects.create(
        name="Podcast activo de detalle",
        slug="podcast-activo-detalle",
        usage_scope="Un episodio de podcast",
        summary="Uso público activo con precio inferior.",
        terms_version="1.0",
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=active_license,
        price=Decimal("29.90"),
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=lower_price_license,
        price=Decimal("12.90"),
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=inactive_license,
        price=Decimal("1.00"),
        is_active=False,
    )

    response = client.get(f"/api/v1/catalog/products/{product.slug}/")

    assert response.status_code == 200
    assert response.json()["preview_url"] is None
    assert response.json()["license_offers"] == [
        {
            "license": {
                "name": lower_price_license.name,
                "slug": lower_price_license.slug,
                "usage_scope": lower_price_license.usage_scope,
                "summary": lower_price_license.summary,
            },
            "price": "12.90",
            "currency": "EUR",
        },
        {
            "license": {
                "name": active_license.name,
                "slug": active_license.slug,
                "usage_scope": active_license.usage_scope,
                "summary": active_license.summary,
            },
            "price": "29.90",
            "currency": "EUR",
        },
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("q", "a" * 101),
        ("category", "categoria-inactiva-api"),
        ("license", "licencia-inactiva-api"),
        ("ordering", "created_at"),
    ],
)
def test_public_product_api_rejects_invalid_known_query_parameters(
    client,
    parameter,
    value,
):
    Category.objects.create(
        name="Categoría inactiva API",
        slug="categoria-inactiva-api",
        is_active=False,
    )
    LicenseType.objects.create(
        name="Licencia inactiva API",
        slug="licencia-inactiva-api",
        usage_scope="Uso inactivo",
        summary="Licencia para validar errores.",
        terms_version="1.0",
        is_active=False,
    )

    response = client.get("/api/v1/catalog/products/", {parameter: value})

    assert response.status_code == 400
    assert response.json() == {
        "error": {"code": "invalid_query_parameter", "parameter": parameter}
    }


@pytest.mark.django_db
@pytest.mark.parametrize("page", ["2", "abc", "0"])
def test_public_product_api_returns_json_for_a_nonexistent_page(client, page):
    response = client.get("/api/v1/catalog/products/", {"page": page})

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "page_not_found"}}


@pytest.mark.django_db
def test_public_product_api_returns_json_for_a_nonexistent_product(client):
    response = client.get("/api/v1/catalog/products/no-existe/")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "product_not_found"}}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "inactive_entities",
    [
        ("product",),
        ("category",),
        ("offer",),
        ("license_type",),
        ("product", "category"),
        ("product", "offer"),
        ("product", "license_type"),
        ("category", "offer"),
        ("category", "license_type"),
        ("offer", "license_type"),
        ("product", "category", "offer"),
        ("product", "category", "license_type"),
        ("product", "offer", "license_type"),
        ("category", "offer", "license_type"),
        ("product", "category", "offer", "license_type"),
    ],
)
def test_public_product_detail_returns_json_404_for_each_unavailable_state(
    client,
    inactive_entities,
):
    case_number = len(inactive_entities)
    category = Category.objects.create(
        name=f"Categoría no disponible API {inactive_entities}",
        slug=f"categoria-no-disponible-api-{case_number}-{'-'.join(inactive_entities)}",
    )
    product = Product.objects.create(
        category=category,
        name=f"Producto no disponible API {inactive_entities}",
        slug=f"producto-no-disponible-api-{case_number}-{'-'.join(inactive_entities)}",
        sku=f"UNAVAILABLE-API-{case_number}",
        summary="Producto para comprobar indisponibilidad del detalle API.",
        description="Producto para comprobar indisponibilidad del detalle API.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    license_type = LicenseType.objects.create(
        name=f"Licencia no disponible API {inactive_entities}",
        slug=f"licencia-no-disponible-api-{case_number}-{'-'.join(inactive_entities)}",
        usage_scope="Uso de prueba",
        summary="Licencia para comprobar indisponibilidad.",
        terms_version="1.0",
    )
    offer = ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )
    entities = {
        "product": product,
        "category": category,
        "offer": offer,
        "license_type": license_type,
    }
    for entity_name in inactive_entities:
        entity = entities[entity_name]
        entity.is_active = False
        entity.save(update_fields=["is_active"])

    response = client.get(f"/api/v1/catalog/products/{product.slug}/")

    assert response.status_code == 404
    assert response["Content-Type"] == "application/json"
    assert response.json() == {"error": {"code": "product_not_found"}}


@pytest.mark.django_db
def test_anonymous_consumer_receives_a_public_product_page(client):
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

    response = client.get("/api/v1/catalog/products/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": product.name,
                "slug": product.slug,
                "summary": product.summary,
                "category": {
                    "name": category.name,
                    "slug": category.slug,
                },
                "duration_ms": product.duration_ms,
                "audio_format": product.audio_format,
                "sample_rate_hz": product.sample_rate_hz,
                "bit_depth": product.bit_depth,
                "minimum_price": "12.90",
                "currency": "EUR",
                "licenses": [
                    {
                        "name": license_type.name,
                        "slug": license_type.slug,
                        "usage_scope": license_type.usage_scope,
                        "summary": license_type.summary,
                    }
                ],
                "detail_url": "/api/v1/catalog/products/nocturnos-urbanos/",
            }
        ],
    }


@pytest.mark.django_db
def test_public_product_page_never_exposes_an_identifiable_private_master(client):
    master_name = "masters/identifiable-private-master.wav"
    category = Category.objects.create(
        name="Ambientes privados",
        slug="ambientes-privados",
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos privados",
        slug="nocturnos-urbanos-privados",
        sku="AMB-PRIVATE-001",
        summary="Ambiente ficticio con archivo maestro privado.",
        description="Grabación preparada para comprobar privacidad.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        master_file=master_name,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales privados",
        slug="youtube-redes-sociales-privados",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )

    response = client.get("/api/v1/catalog/products/")
    response_content = response.content.decode()

    assert response.status_code == 200
    assert "master_file" not in response_content
    assert master_name not in response_content
    assert Path(master_name).name not in response_content
    assert str(product.master_file.storage.location) not in response_content


@pytest.mark.django_db
def test_public_product_detail_never_exposes_an_identifiable_private_master(client):
    master_name = "masters/detail-identifiable-private-master.wav"
    category = Category.objects.create(
        name="Ambientes de detalle privados",
        slug="ambientes-detalle-privados",
    )
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos de detalle privados",
        slug="nocturnos-urbanos-detalle-privados",
        sku="AMB-DETAIL-PRIVATE-001",
        summary="Ambiente ficticio para comprobar privacidad del detalle.",
        description="Grabación preparada para comprobar privacidad del detalle.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
        master_file=master_name,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales de detalle privados",
        slug="youtube-redes-sociales-detalle-privados",
        usage_scope="Un canal por plataforma",
        summary="Uso público para comprobar privacidad del detalle.",
        terms_version="1.0",
    )
    ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )

    response = client.get(f"/api/v1/catalog/products/{product.slug}/")
    response_content = response.content.decode()

    assert response.status_code == 200
    assert "master_file" not in response_content
    assert master_name not in response_content
    assert Path(master_name).name not in response_content
    assert str(product.master_file.storage.location) not in response_content
