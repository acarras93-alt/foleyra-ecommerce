from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import close_old_connections
from django.urls import reverse
from pytest_django.asserts import assertContains

from apps.cart.models import CartItem
from apps.cart.services import add_offer_to_cart
from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer
from apps.orders.models import LicenseGrant, Order, OrderItem, PaymentAttempt
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
    assert OrderItem.objects.filter(order=order).count() == 1
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

    order.refresh_from_db(from_queryset=None)
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


@pytest.mark.django_db
def test_approved_payment_issues_one_permission_per_order_item(client):
    # Preparar: usuario autenticado
    owner = get_user_model().objects.create_user(
        username="payment-owner", password="ReliablePassword123!"
    )
    client.force_login(owner)

    # Preparar pedido con varias líneas históricas
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    first_item = OrderItem.objects.create(
        order=order,
        product_name="Impacto cinematográfico",
        product_sku="PED-001",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )

    second_item = OrderItem.objects.create(
        order=order,
        product_name="Pasos sobre madera",
        product_sku="PED-002",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("8.50"),
        currency="EUR",
    )

    third_item = OrderItem.objects.create(
        order=order,
        product_name="Lluvia exterior",
        product_sku="PED-003",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("9.90"),
        currency="EUR",
    )

    # Contiene una copia de los valores anteriores al pago
    items_before = list(OrderItem.objects.filter(order=order).order_by("pk").values())

    # Actuar: solicitar la aprobación y seguir la redirección.
    payment_key = uuid4()

    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    response = client.post(
        payment_url,
        {
            "result": "approved",
            "idempotency_key": str(payment_key),
        },
        follow=True,
    )

    # Devolverse: redirección al detalle y página accesible.
    assert response.redirect_chain == [(detail_url, 302)]
    assert response.status_code == 200

    # Cambiar: el pedido queda pagado, conservando propietario e importe.
    order.refresh_from_db(from_queryset=None)

    assert order.status == Order.Status.PAID
    assert order.owner == owner
    assert order.total_amount == Decimal("12.90")
    assert order.currency == "EUR"

    # Crear: exactamente un intento aprobado con los datos esperados.
    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == "approved"
    assert attempt.idempotency_key == payment_key
    assert attempt.amount == Decimal("12.90")
    assert attempt.currency == "EUR"
    assert attempt.created_at is not None

    # Conservar: las líneas históricas permanecen intactas.
    items_after = list(OrderItem.objects.filter(order=order).order_by("pk").values())
    assert items_after == items_before

    # Mostrar: resultado, estado y datos históricos en el detalle.
    expected_message = "Pago simulado aprobado."

    assert expected_message in [
        message.message for message in get_messages(response.wsgi_request)
    ]
    assertContains(response, expected_message)
    assertContains(response, "Estado: Paid")
    assertContains(response, "Producto: Impacto cinematográfico")
    assertContains(response, "SKU: PED-001")
    assertContains(response, "Licencia: Licencia comercial")
    assertContains(response, "Términos: 1.0")
    assertContains(response, "Precio: 12,90 EUR")

    grants = list(
        LicenseGrant.objects.filter(order_item__order=order)
        .select_related("order_item__order__owner")
        .order_by("pk")
    )

    # Compruebar cantidad, correspondencia con las tres líneas, estado activo y propietario
    assert len(grants) == 3

    expected_item_ids = {first_item.pk, second_item.pk, third_item.pk}
    actual_item_ids = {grant.order_item.pk for grant in grants}

    assert actual_item_ids == expected_item_ids

    for grant in grants:
        assert grant.status == LicenseGrant.Status.ACTIVE
        assert grant.order_item.order.owner.pk == owner.pk
        assert grant.issued_at is not None


@pytest.mark.django_db
def test_payment_replay_with_same_key_preserves_existing_license_grants(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="license-replay-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Preparar: pedido pendiente con dos líneas históricas.
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("21.40"),
        currency="EUR",
    )

    OrderItem.objects.create(
        order=order,
        product_name="Impacto cinematográfico",
        product_sku="PED-001",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )

    OrderItem.objects.create(
        order=order,
        product_name="Pasos sobre madera",
        product_sku="PED-002",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("8.50"),
        currency="EUR",
    )

    # Preparar: misma URL y mismos datos para ambas solicitudes.
    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    payment_key = uuid4()
    payment_data = {
        "result": "approved",
        "idempotency_key": str(payment_key),
    }

    # Actuar: aprobar el pago por primera vez.
    first_response = client.post(
        payment_url,
        payment_data,
        follow=True,
    )

    assert first_response.redirect_chain == [(detail_url, 302)]
    assert first_response.status_code == 200

    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    # Guardar: derechos emitidos, incluidos sus identificadores y fechas.
    grants_before = list(
        LicenseGrant.objects.filter(order_item__order=order).order_by("pk").values()
    )

    assert len(grants_before) == 2
    assert all(grant["status"] == LicenseGrant.Status.ACTIVE for grant in grants_before)

    original_attempt = PaymentAttempt.objects.get(order=order)

    # Actuar: repetir la aprobación con la misma clave.
    repeated_response = client.post(
        payment_url,
        payment_data,
        follow=True,
    )

    # Comprobar: la repetición conserva la respuesta de éxito.
    assert repeated_response.redirect_chain == [(detail_url, 302)]
    assert repeated_response.status_code == 200

    # Comprobar: siguen existiendo exactamente los mismos derechos.
    grants_after = list(
        LicenseGrant.objects.filter(order_item__order=order).order_by("pk").values()
    )

    assert len(grants_after) == 2
    assert grants_after == grants_before

    # Comprobar: el pedido sigue pagado y conserva el intento original.
    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1
    assert attempts.get().pk == original_attempt.pk


@pytest.mark.django_db
def test_order_preserves_license_conditions_after_catalog_changes(client):
    pass
