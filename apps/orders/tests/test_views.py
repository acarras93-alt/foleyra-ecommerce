from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse

from apps.cart.models import CartItem
from apps.cart.services import add_offer_to_cart
from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer
from apps.orders.models import Order


def create_available_offer():
    category = Category.objects.create(name="Pedidos web", slug="pedidos-web")
    product = Product.objects.create(
        category=category,
        name="Impacto web",
        slug="impacto-web",
        sku="PED-WEB-001",
        summary="Impacto de prueba web.",
        description="Descripción de prueba web.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    license_type = LicenseType.objects.create(
        name="Licencia web",
        slug="licencia-web",
        usage_scope="Uso de prueba web",
        summary="Resumen de licencia de prueba web.",
        terms_version="1.0",
    )
    return ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )


@pytest.mark.django_db
def test_order_conversion_rejects_get_and_anonymous_posts_without_changes():
    client = Client(enforce_csrf_checks=True)
    order_create_url = reverse("orders:create")

    get_response = client.get(order_create_url)
    csrf_failure_response = client.post(order_create_url)
    client.get(reverse("users:login"))
    csrf_token = client.cookies["csrftoken"].value
    anonymous_response = client.post(
        order_create_url,
        {"csrfmiddlewaretoken": csrf_token},
    )

    assert get_response.status_code == 405
    assert csrf_failure_response.status_code == 403
    assert anonymous_response.status_code == 302
    assert anonymous_response["Location"] == f"{reverse('users:login')}?next=/cart/"
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_authenticated_user_converts_own_cart_and_is_redirected_with_success_message(
    client,
):
    owner = get_user_model().objects.create_user(
        username="web-order-owner",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    client.force_login(owner)

    response = client.post(reverse("orders:create"), follow=True)

    assert response.redirect_chain == [(reverse("cart:detail"), 302)]
    assert Order.objects.filter(owner=owner).count() == 1
    assert not CartItem.objects.filter(cart__owner=owner).exists()
    assert [message.message for message in get_messages(response.wsgi_request)] == [
        "Pedido creado."
    ]


@pytest.mark.django_db
def test_authenticated_user_with_empty_cart_receives_conflict_without_order(client):
    owner = get_user_model().objects.create_user(
        username="web-empty-order-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    response = client.post(reverse("orders:create"))

    assert response.status_code == 409
    assert not Order.objects.filter(owner=owner).exists()


@pytest.mark.django_db
def test_authenticated_user_with_unavailable_offer_receives_conflict_and_keeps_cart(
    client,
):
    owner = get_user_model().objects.create_user(
        username="web-unavailable-order-owner",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    cart_item, _ = add_offer_to_cart(owner=owner, offer_id=offer.pk)
    offer.is_active = False
    offer.save(update_fields=["is_active"])
    client.force_login(owner)

    response = client.post(reverse("orders:create"))

    assert response.status_code == 409
    assert not Order.objects.filter(owner=owner).exists()
    assert CartItem.objects.filter(pk=cart_item.pk).exists()
