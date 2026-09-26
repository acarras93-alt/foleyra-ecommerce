from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains

from apps.cart.models import Cart, CartItem
from apps.cart.services import add_offer_to_cart
from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer
from apps.orders.models import Order, OrderItem
from apps.orders.services import create_order_from_cart


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


@pytest.mark.parametrize(
    ("path", "expected_next"),
    [
        ("/orders/", "/orders/"),
        ("/orders/1/", "/orders/1/"),
    ],
)
def test_anonymous_visitor_is_redirected_to_login_when_consulting_orders(
    client,
    path,
    expected_next,
):
    response = client.get(path)

    assert response.status_code == 302
    assert response.url == f"{reverse('users:login')}?next={expected_next}"


@pytest.mark.django_db
def test_authenticated_user_without_orders_sees_empty_order_list(client):
    owner = get_user_model().objects.create_user(
        username="empty-order-list-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    response = client.get(reverse("orders:list"))

    assert response.status_code == 200
    assert "No tienes pedidos" in response.content.decode()


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


@pytest.mark.django_db
def test_authenticated_user_sees_own_order_fields_in_list(client):
    owner = get_user_model().objects.create_user(
        username="web-order-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    response = client.get(reverse("orders:list"))

    assert response.status_code == 200
    assertContains(response, f"Pedido #{order.pk}")
    assertContains(response, "Pending payment")
    assertContains(response, "12,90")
    assertContains(response, order.currency)
    expected_date = timezone.localtime(order.created_at).strftime("%d/%m/%Y %H:%M")
    assertContains(response, f"<time>{expected_date}</time>", html=True)
    detail_url = reverse("orders:detail", kwargs={"order_id": order.pk})
    assertContains(response, f'<a href="{detail_url}">Ver detalle</a>', html=True)


@pytest.mark.django_db
def test_order_list_excludes_other_users_orders(client):

    owner = get_user_model().objects.create_user(
        username="web-order-owner",
        password="ReliablePassword123!",
    )

    other_user = get_user_model().objects.create_user(
        username="other-order-owner",
        password="ReliablePassword123!",
    )

    client.force_login(owner)

    own_order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    other_order = Order.objects.create(
        owner=other_user,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    response = client.get(reverse("orders:list"))

    assert response.status_code == 200
    assertContains(response, f"Pedido #{own_order.pk} —")
    assertNotContains(response, f"Pedido #{other_order.pk} —")


@pytest.mark.django_db
def test_authenticated_user_sees_own_order_detail_with_historical_items(client):
    owner = get_user_model().objects.create_user(
        username="web-order-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    order_item = OrderItem.objects.create(
        order=order,
        product_name="Impacto cinematográfico",
        product_sku="PED-001",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )

    response = client.get(reverse("orders:detail", kwargs={"order_id": order.pk}))

    assert response.status_code == 200

    # Datos del pedido
    assertContains(response, "Pending payment")
    assertContains(response, "Total: 12,90 EUR")

    # Datos históricos de la línea
    assertContains(response, order_item.product_name)
    assertContains(response, order_item.product_sku)
    assertContains(response, order_item.license_name)
    assertContains(response, "Términos: 1.0")
    assertContains(response, "Precio: 12,90 EUR")


@pytest.mark.django_db
def test_order_detail_returns_same_404_for_foreign_and_missing_orders(client, settings):
    settings.DEBUG = False

    owner = get_user_model().objects.create_user(
        username="detail-owner",
        password="ReliablePassword123!",
    )
    other_user = get_user_model().objects.create_user(
        username="detail-other-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    other_order = Order.objects.create(
        owner=other_user,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )
    OrderItem.objects.create(
        order=other_order,
        product_name="Producto privado del otro cliente",
        product_sku="PRIVADO-001",
        license_name="Licencia privada",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )

    missing_id = other_order.pk + 1
    assert not Order.objects.filter(pk=missing_id).exists()

    foreign_response = client.get(
        reverse("orders:detail", kwargs={"order_id": other_order.pk})
    )
    missing_response = client.get(
        reverse("orders:detail", kwargs={"order_id": missing_id})
    )

    assert foreign_response.status_code == 404
    assert missing_response.status_code == 404
    assert foreign_response.content == missing_response.content

    assertNotContains(
        foreign_response,
        "Producto privado del otro cliente",
        status_code=404,
    )
    assertNotContains(
        foreign_response,
        "PRIVADO-001",
        status_code=404,
    )


@pytest.mark.django_db
def test_order_detail_preserves_snapshot_after_catalog_changes(client):
    # Preparar usuario autenticado y catalogo original.
    owner = get_user_model().objects.create_user(
        username="historical-order-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)
    offer = create_available_offer()

    # Crear el pedido con la copia histórica del catálogo.
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    # Modificar y guardar el catálogo después de crear el pedido.
    product = offer.product
    product.name = "Producto modificado"
    product.sku = "SKU-NUEVO-999"
    product.save(update_fields=["name", "sku"])

    license_type = offer.license_type
    license_type.name = "Licencia modificada"
    license_type.terms_version = "2.0"
    license_type.save(update_fields=["name", "terms_version"])

    offer.price = Decimal("99.50")
    offer.save(update_fields=["price"])

    # Consultar el detalle del pedido histórico
    response = client.get(reverse("orders:detail", kwargs={"order_id": order.pk}))

    # Comprobar que aparecen los valores originales
    assert response.status_code == 200
    assertContains(response, "Producto: Impacto web")
    assertContains(response, "SKU: PED-WEB-001")
    assertContains(response, "Licencia: Licencia web")
    assertContains(response, "Términos: 1.0")
    assertContains(response, "Precio: 12,90 EUR")
    assertContains(response, "Total: 12,90 EUR")

    # Comprobar que no aparecen los valores nuevos
    assertNotContains(response, "Producto modificado")
    assertNotContains(response, "SKU-NUEVO-999")
    assertNotContains(response, "Licencia modificada")
    assertNotContains(response, "Términos: 2.0")
    assertNotContains(response, "99,50")


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["orders:list", "orders:detail"])
def test_order_read_does_not_change_business_data(client, view_name):
    # Usuario autenticado
    owner = get_user_model().objects.create_user(
        username="web-order-owner",
        password="ReliablePassword123!",
    )

    client.force_login(owner)

    # Pedido propio(Order)
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    # Linea historica asociada(OrderItem)
    OrderItem.objects.create(
        order=order,
        product_name="Impacto cinematográfico",
        product_sku="PED-001",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )

    # Carrito con una oferta
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)

    # Estado de los datos antes de consultar.
    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }
    # Solicitar el listado o el detalle según esta ejecución.
    if view_name == "orders:detail":
        url = reverse(view_name, kwargs={"order_id": order.pk})
    else:
        url = reverse(view_name)

    response = client.get(url)

    # Volver a leer los datos desde la base de datos.
    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    # Comprobar que la consulta funciona y deja los datos intactos
    assert response.status_code == 200
    assert after == before


@pytest.mark.django_db
def test_order_list_orders_by_creation_date_and_id_descending(client):
    owner = get_user_model().objects.create_user(
        username="ordered-list-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    recent_lower_id = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("10.00"),
        currency="EUR",
    )
    recent_higher_id = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("20.00"),
        currency="EUR",
    )

    # Se crea al final para tener el ID mayor,
    # pero le asignaremos la fecha más antigua.
    older_order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("30.00"),
        currency="EUR",
    )

    # Establecer un empate exacto entre los dos pedidos recientes.
    recent_date = timezone.now()

    Order.objects.filter(pk__in=[recent_lower_id.pk, recent_higher_id.pk]).update(
        created_at=recent_date
    )

    Order.objects.filter(pk=older_order.pk).update(
        created_at=recent_date - timedelta(days=1)
    )

    response = client.get(reverse("orders:list"))

    assert response.status_code == 200

    html = response.content.decode()
    higher_id_position = html.index(f"Pedido #{recent_higher_id.pk} —")
    lower_id_position = html.index(f"Pedido #{recent_lower_id.pk} —")
    older_position = html.index(f"Pedido #{older_order.pk} —")

    assert higher_id_position < lower_id_position < older_position


@pytest.mark.django_db
def test_order_detail_query_count_does_not_grow_with_items(client):
    owner = get_user_model().objects.create_user(
        username="order-query-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    query_counts = []

    for item_count in (1, 10):
        # Preparar el pedido y sus líneas fuera de la medición.
        order = Order.objects.create(
            owner=owner,
            status=Order.Status.PENDING_PAYMENT,
            total_amount=Decimal("12.90") * item_count,
            currency="EUR",
        )

        items = []
        for index in range(item_count):
            item = OrderItem.objects.create(
                order=order,
                product_name=f"Producto histórico {index:02d}",
                product_sku=f"HIST-{index:02d}",
                license_name="Licencia comercial",
                terms_version="1.0",
                price=Decimal("12.90"),
                currency="EUR",
            )
            items.append(item)

        url = reverse("orders:detail", kwargs={"order_id": order.pk})

        # Contar las consultas de la petición y del renderizado.
        with CaptureQueriesContext(connection) as queries:
            response = client.get(url)

        query_counts.append(len(queries))

        assert response.status_code == 200

        # Comprobar que todas las líneas se han mostrado realmente.
        for item in items:
            assertContains(
                response,
                f"Producto: {item.product_name}</p>",
                count=1,
            )
            assertContains(
                response,
                f"SKU: {item.product_sku}</p>",
                count=1,
            )

    # Una línea y diez líneas deben requerir las mismas consultas.
    assert query_counts[0] == query_counts[1], query_counts

    # Presupuesto de consultas para la configuración actual.
    assert query_counts[1] <= 4, query_counts


@pytest.mark.django_db
def test_authenticated_user_sees_orders_link_in_main_navigation(client):
    owner = get_user_model().objects.create_user(
        username="orders-navigation-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    response = client.get(reverse("core:home"))

    assert response.status_code == 200

    expected_link = f'<a href="{reverse("orders:list")}">Mis pedidos</a>'
    assertContains(response, expected_link, html=True)
