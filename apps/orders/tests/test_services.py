from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections

from apps.cart.models import CartItem
from apps.cart.services import add_offer_to_cart
from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer
from apps.orders.models import Order, OrderItem
from apps.orders.services import EmptyCart, OfferNotAvailable, create_order_from_cart


def create_available_offer():
    category = Category.objects.create(name="Pedidos", slug="pedidos")
    product = Product.objects.create(
        category=category,
        name="Impacto cinematográfico",
        slug="impacto-cinematografico",
        sku="PED-001",
        summary="Impacto de prueba.",
        description="Descripción de prueba para pedido.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    license_type = LicenseType.objects.create(
        name="Licencia de pedido",
        slug="licencia-pedido",
        usage_scope="Uso de prueba",
        summary="Resumen de licencia de prueba.",
        terms_version="1.0",
    )
    return ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )


@pytest.mark.django_db
def test_converting_an_owners_available_cart_creates_pending_order_and_empties_cart():
    owner = get_user_model().objects.create_user(
        username="order-owner",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)

    order = create_order_from_cart(owner=owner)

    assert order.owner == owner
    assert order.status == Order.Status.PENDING_PAYMENT
    assert order.total_amount == Decimal("12.90")
    assert order.currency == "EUR"
    assert order.items.count() == 1
    assert not CartItem.objects.filter(cart__owner=owner).exists()


@pytest.mark.django_db
def test_order_lines_preserve_the_catalog_values_captured_at_conversion():
    owner = get_user_model().objects.create_user(
        username="snapshot-order-owner",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)

    order = create_order_from_cart(owner=owner)
    offer.product.sku = "PED-002"
    offer.product.name = "Impacto modificado"
    offer.product.save(update_fields=["sku", "name"])
    offer.license_type.name = "Licencia modificada"
    offer.license_type.terms_version = "2.0"
    offer.license_type.save(update_fields=["name", "terms_version"])
    offer.price = Decimal("20.00")
    offer.currency = "USD"
    offer.save(update_fields=["price", "currency"])

    order.refresh_from_db()
    order_item = OrderItem.objects.get(order=order)

    assert order.total_amount == Decimal("12.90")
    assert order.currency == "EUR"
    assert order_item.product_sku == "PED-001"
    assert order_item.product_name == "Impacto cinematográfico"
    assert order_item.license_name == "Licencia de pedido"
    assert order_item.terms_version == "1.0"
    assert order_item.price == Decimal("12.90")
    assert order_item.currency == "EUR"


@pytest.mark.django_db
def test_converting_an_empty_cart_creates_no_order():
    owner = get_user_model().objects.create_user(
        username="empty-order-owner",
        password="ReliablePassword123!",
    )

    with pytest.raises(EmptyCart):
        create_order_from_cart(owner=owner)

    assert not Order.objects.filter(owner=owner).exists()


@pytest.mark.django_db
def test_converting_a_cart_with_an_unavailable_offer_preserves_the_cart():
    owner = get_user_model().objects.create_user(
        username="unavailable-order-owner",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    cart_item, _ = add_offer_to_cart(owner=owner, offer_id=offer.pk)
    offer.is_active = False
    offer.save(update_fields=["is_active"])

    with pytest.raises(OfferNotAvailable):
        create_order_from_cart(owner=owner)

    assert not Order.objects.filter(owner=owner).exists()
    assert CartItem.objects.filter(pk=cart_item.pk).exists()


@pytest.mark.django_db
def test_failure_creating_order_items_rolls_back_order_and_preserves_cart(monkeypatch):
    owner = get_user_model().objects.create_user(
        username="rollback-order-owner",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    cart_item, _ = add_offer_to_cart(owner=owner, offer_id=offer.pk)

    def raise_creation_failure(*args, **kwargs):
        raise RuntimeError("Order item creation failed")

    monkeypatch.setattr(OrderItem.objects, "bulk_create", raise_creation_failure)

    with pytest.raises(RuntimeError, match="Order item creation failed"):
        create_order_from_cart(owner=owner)

    assert not Order.objects.filter(owner=owner).exists()
    assert CartItem.objects.filter(pk=cart_item.pk).exists()


@pytest.mark.django_db
def test_converting_one_owners_cart_does_not_change_another_owners_cart():
    first_owner = get_user_model().objects.create_user(
        username="first-order-owner",
        password="ReliablePassword123!",
    )
    second_owner = get_user_model().objects.create_user(
        username="second-order-owner",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    add_offer_to_cart(owner=first_owner, offer_id=offer.pk)
    second_cart_item, _ = add_offer_to_cart(owner=second_owner, offer_id=offer.pk)

    order = create_order_from_cart(owner=first_owner)

    assert order.owner == first_owner
    assert not CartItem.objects.filter(cart__owner=first_owner).exists()
    assert CartItem.objects.filter(pk=second_cart_item.pk).exists()
    assert not Order.objects.filter(owner=second_owner).exists()


@pytest.mark.django_db(transaction=True)
def test_two_conversions_of_the_same_cart_create_one_order_without_duplicate_lines():
    owner = get_user_model().objects.create_user(
        username="concurrent-order-owner",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    barrier = Barrier(2)

    def convert_cart():
        close_old_connections()
        try:
            barrier.wait()
            order = create_order_from_cart(owner=owner)
            return "created", order.pk
        except EmptyCart:
            return "empty", None
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: convert_cart(), range(2)))

    assert sorted(result[0] for result in results) == ["created", "empty"]
    assert Order.objects.filter(owner=owner).count() == 1
    assert OrderItem.objects.get(order__owner=owner).price == Decimal("12.90")
    assert not CartItem.objects.filter(cart__owner=owner).exists()
