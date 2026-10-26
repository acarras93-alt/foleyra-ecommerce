from decimal import Decimal

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer

CATALOG_MODELS = (Category, Product, LicenseType, ProductLicenseOffer)


def grant_catalog_permissions(user, *, actions=("add", "change", "view")):
    permissions = []
    for model in CATALOG_MODELS:
        content_type = ContentType.objects.get_for_model(model)
        permissions.extend(
            Permission.objects.filter(
                content_type=content_type,
                codename__in=[
                    f"{action}_{model._meta.model_name}" for action in actions
                ],
            )
        )
    user.user_permissions.add(*permissions)


def create_catalog_staff():
    user = get_user_model().objects.create_user(
        username="catalog-admin",
        password="ReliablePassword123!",
        is_staff=True,
    )
    grant_catalog_permissions(user)
    return user


def post_admin_change(client, url_name, object_id, data):
    data = {**data, "_save": "Guardar"}
    return client.post(reverse(url_name, args=[object_id]), data)


def create_catalog_data(*, suffix=""):
    category = Category.objects.create(
        name=f"Ambientes {suffix}".strip(),
        slug=f"ambientes-{suffix or 'base'}",
    )
    license_type = LicenseType.objects.create(
        name=f"Licencia audiovisual {suffix}".strip(),
        slug=f"licencia-audiovisual-{suffix or 'base'}",
        usage_scope="Una producción audiovisual",
        summary="Uso sincronizado en una producción.",
        terms_version="1.0",
        terms_text="Condiciones iniciales.",
    )
    product = Product.objects.create(
        category=category,
        name=f"Paisaje sonoro {suffix}".strip(),
        slug=f"paisaje-sonoro-{suffix or 'base'}",
        sku=f"ADM-{suffix or 'BASE'}",
        summary="Paisaje sonoro para pruebas administrativas.",
        description="Descripción del producto administrable.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    offer = ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )
    return category, license_type, product, offer


@pytest.mark.django_db
def test_catalog_staff_can_create_and_modify_all_catalog_entities(client):
    user = create_catalog_staff()
    client.force_login(user)

    category_response = client.post(
        reverse("admin:catalog_category_add"),
        {
            "name": "Foley urbano",
            "slug": "foley-urbano",
            "description": "Categoría administrada.",
            "is_active": "on",
            "_save": "Guardar",
        },
    )
    category = Category.objects.get(slug="foley-urbano")

    product_response = client.post(
        reverse("admin:catalog_product_add"),
        {
            "category": category.pk,
            "name": "Pasos sobre grava",
            "slug": "pasos-sobre-grava",
            "sku": "ADM-GRAVA",
            "summary": "Pasos sobre grava para una escena.",
            "description": "Descripción completa de los pasos.",
            "duration_ms": "12000",
            "audio_format": "wav",
            "sample_rate_hz": "48000",
            "bit_depth": "24",
            "is_active": "on",
            "_save": "Guardar",
        },
    )
    product = Product.objects.get(sku="ADM-GRAVA")

    license_response = client.post(
        reverse("admin:catalog_licensetype_add"),
        {
            "name": "Licencia para cine",
            "slug": "licencia-para-cine",
            "usage_scope": "Una película",
            "summary": "Uso en una película.",
            "terms_version": "1.0",
            "terms_text": "Condiciones para cine.",
            "is_active": "on",
            "_save": "Guardar",
        },
    )
    license_type = LicenseType.objects.get(slug="licencia-para-cine")

    offer_response = client.post(
        reverse("admin:catalog_productlicenseoffer_add"),
        {
            "product": product.pk,
            "license_type": license_type.pk,
            "price": "24.90",
            "grantor_name": "Foleyra",
            "rights_holder_name": "Foleyra",
            "is_active": "on",
            "_save": "Guardar",
        },
    )
    offer = ProductLicenseOffer.objects.get(product=product, license_type=license_type)

    category_response = post_admin_change(
        client,
        "admin:catalog_category_change",
        category.pk,
        {
            "name": "Foley urbano actualizado",
            "slug": category.slug,
            "description": category.description,
            "is_active": "on",
        },
    )
    license_response = post_admin_change(
        client,
        "admin:catalog_licensetype_change",
        license_type.pk,
        {
            "name": license_type.name,
            "slug": license_type.slug,
            "usage_scope": "Dos películas",
            "summary": license_type.summary,
            "terms_version": "2.0",
            "terms_text": "Condiciones actualizadas para cine.",
            "is_active": "on",
        },
    )
    product_response = post_admin_change(
        client,
        "admin:catalog_product_change",
        product.pk,
        {
            "category": category.pk,
            "name": "Pasos sobre grava actualizados",
            "slug": product.slug,
            "sku": product.sku,
            "summary": product.summary,
            "description": product.description,
            "duration_ms": product.duration_ms,
            "audio_format": product.audio_format,
            "sample_rate_hz": product.sample_rate_hz,
            "bit_depth": product.bit_depth,
            "is_active": "on",
        },
    )
    offer_response = post_admin_change(
        client,
        "admin:catalog_productlicenseoffer_change",
        offer.pk,
        {
            "product": product.pk,
            "license_type": license_type.pk,
            "price": "29.90",
            "grantor_name": offer.grantor_name,
            "rights_holder_name": offer.rights_holder_name,
            "is_active": "on",
        },
    )

    category.refresh_from_db()
    license_type.refresh_from_db()
    product.refresh_from_db()
    offer.refresh_from_db()
    assert category_response.status_code == 302
    assert license_response.status_code == 302
    assert product_response.status_code == 302
    assert offer_response.status_code == 302
    assert category.name == "Foley urbano actualizado"
    assert license_type.terms_version == "2.0"
    assert license_type.usage_scope == "Dos películas"
    assert product.name == "Pasos sobre grava actualizados"
    assert offer.price == Decimal("29.90")


@pytest.mark.django_db
def test_admin_rejects_license_terms_change_without_new_version(client):
    _, license_type, _, _ = create_catalog_data()
    user = create_catalog_staff()
    client.force_login(user)

    response = post_admin_change(
        client,
        "admin:catalog_licensetype_change",
        license_type.pk,
        {
            "name": license_type.name,
            "slug": license_type.slug,
            "usage_scope": license_type.usage_scope,
            "summary": license_type.summary,
            "terms_version": license_type.terms_version,
            "terms_text": "Condiciones modificadas sin versión nueva.",
            "is_active": "on",
        },
    )

    license_type.refresh_from_db()
    assert response.status_code == 200
    assert "Debes indicar una nueva versión" in response.content.decode()
    assert license_type.terms_text == "Condiciones iniciales."


@pytest.mark.django_db
def test_admin_deactivation_removes_product_from_web_and_api(client):
    category, license_type, product, offer = create_catalog_data()
    user = create_catalog_staff()
    client.force_login(user)

    response = post_admin_change(
        client,
        "admin:catalog_product_change",
        product.pk,
        {
            "category": category.pk,
            "name": product.name,
            "slug": product.slug,
            "sku": product.sku,
            "summary": product.summary,
            "description": product.description,
            "duration_ms": product.duration_ms,
            "audio_format": product.audio_format,
            "sample_rate_hz": product.sample_rate_hz,
            "bit_depth": product.bit_depth,
        },
    )

    product.refresh_from_db()
    public_client = Client()
    web_response = public_client.get(reverse("catalog:product-list"))
    api_response = public_client.get(reverse("catalog_api:product-list"))
    assert response.status_code == 302
    assert not product.is_active
    assert product.name not in web_response.content.decode()
    assert product.slug not in str(api_response.json())
    assert offer.is_active
    assert license_type.is_active


@pytest.mark.django_db
@pytest.mark.parametrize("entity", ["category", "offer"])
def test_admin_deactivation_of_category_or_offer_removes_product_from_public_catalog(
    client,
    entity,
):
    category, license_type, product, offer = create_catalog_data(suffix=entity)
    user = create_catalog_staff()
    client.force_login(user)

    if entity == "category":
        response = post_admin_change(
            client,
            "admin:catalog_category_change",
            category.pk,
            {
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
            },
        )
    else:
        response = post_admin_change(
            client,
            "admin:catalog_productlicenseoffer_change",
            offer.pk,
            {
                "product": product.pk,
                "license_type": license_type.pk,
                "price": offer.price,
                "grantor_name": offer.grantor_name,
                "rights_holder_name": offer.rights_holder_name,
            },
        )

    public_client = Client()
    web_response = public_client.get(reverse("catalog:product-list"))
    api_response = public_client.get(reverse("catalog_api:product-list"))
    assert response.status_code == 302
    assert product.name not in web_response.content.decode()
    assert product.slug not in str(api_response.json())


@pytest.mark.django_db
def test_catalog_admin_lists_are_searchable_and_do_not_expose_private_master(
    client,
):
    category, _, product, _ = create_catalog_data()
    product.master_file = "masters/private-admin-master.wav"
    product.save(update_fields=["master_file"])
    other_product = Product.objects.create(
        category=category,
        name="Otro producto",
        slug="otro-producto",
        sku="ADM-OTRO",
        summary="Otro resumen.",
        description="Otra descripción.",
        duration_ms=10_000,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    user = create_catalog_staff()
    client.force_login(user)

    list_response = client.get(
        reverse("admin:catalog_product_changelist"),
        {"q": product.sku},
    )
    change_response = client.get(
        reverse("admin:catalog_product_change", args=[product.pk]),
    )

    list_content = list_response.content.decode()
    change_content = change_response.content.decode()
    assert product.name in list_content
    assert other_product.name not in list_content
    assert product.sku in list_content
    assert "private-admin-master.wav" not in list_content
    assert "master_file" not in change_content
    assert "private-admin-master.wav" not in change_content


@pytest.mark.django_db
def test_product_admin_list_loads_related_categories_without_n_plus_one(client):
    category, _, _, _ = create_catalog_data()
    for number in range(2, 4):
        Product.objects.create(
            category=category,
            name=f"Producto {number}",
            slug=f"producto-{number}",
            sku=f"ADM-{number}",
            summary="Resumen.",
            description="Descripción.",
            duration_ms=10_000,
            audio_format="wav",
            sample_rate_hz=48_000,
            bit_depth=24,
        )
    user = create_catalog_staff()
    client.force_login(user)

    with CaptureQueriesContext(connection) as queries:
        response = client.get(reverse("admin:catalog_product_changelist"))

    assert response.status_code == 200
    assert len(queries) < 20
    assert admin.site._registry[Product].list_select_related == ("category",)
