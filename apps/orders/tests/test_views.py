import re
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import connection, connections
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains

from apps.cart.models import Cart, CartItem
from apps.cart.services import add_offer_to_cart
from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer
from apps.orders.models import Order, OrderItem, PaymentAttempt
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

    # RF-08 añade una consulta fija para cargar el historial de intentos.
    assert query_counts[1] <= 5, query_counts


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


@pytest.mark.django_db
def test_pending_order_detail_shows_payment_form_without_business_changues(client):
    # Preparación del usuario
    owner = get_user_model().objects.create_user(
        username="web-order-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Preparación del pedido propio(Order)
    order = Order.objects.create(
        owner=owner,  # a quien pertenece
        status=Order.Status.PENDING_PAYMENT,  # en que estado esta
        total_amount=Decimal("12.90"),  # cual es su importe
        currency="EUR",  # en que moneda
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
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    url = reverse("orders:detail", kwargs={"order_id": order.pk})

    response = client.get(url)

    # Volver a leer los datos desde la base de datos.
    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    assert response.status_code == 200
    assert before == after

    # Localizar el formulario dirigido al pago de este pedido.
    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    forms = re.findall(
        r"<form\b([^>]*)>(.*?)</form>",
        response.content.decode(),
        flags=re.DOTALL | re.IGNORECASE,
    )

    payment_forms = [
        (attributes, content)
        for attributes, content in forms
        if re.search(
            rf"""action=["']{re.escape(payment_url)}["']""",
            attributes,
        )
    ]

    assert len(payment_forms) == 1, "Debe existir un formulario de pago"
    attributes, content = payment_forms[0]

    # El formulario envía la operación mediante POST.
    assert re.search(r"""method=["']post["']""", attributes, re.IGNORECASE)

    # Obtener los campos ocultos del formulario.
    inputs = re.findall(r"<input\b[^>]*>", content, re.IGNORECASE)

    def hidden_value(name):
        matching = [
            tag for tag in inputs if re.search(rf"""name=["']{name}["']""", tag)
        ]
        assert len(matching) == 1, f"Falta el campo único {name}"
        assert re.search(r"""type=["']hidden["']""", matching[0])
        value = re.search(r"""value=["']([^"']+)["']""", matching[0])
        assert value, f"El campo {name} debe tener un valor"
        return value.group(1)

    # El token está presente y la clave tiene formato UUID.
    assert hidden_value("csrfmiddlewaretoken")
    UUID(hidden_value("idempotency_key"))

    # El formulario solicita una aprobación simulada.
    assert hidden_value("result") == "approved"


@pytest.mark.parametrize(
    ("method", "with_csrf", "expected_status"),
    [
        ("post", True, 302),
        ("post", False, 403),
        ("get", False, 405),
    ],
)
@pytest.mark.django_db
def test_payment_simulation_rejects_unauthorized_requests_without_business_changes(
    method, with_csrf, expected_status
):
    owner = get_user_model().objects.create_user(
        username="web-order-owner",
        password="ReliablePassword123!",
    )

    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    client = Client(enforce_csrf_checks=True)
    url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )

    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }

    data = {
        "result": "approved",
        "idempotency_key": str(uuid4()),
    }

    if with_csrf:
        client.get(reverse("users:login"))
        csrf_token = client.cookies["csrftoken"].value
        data["csrfmiddlewaretoken"] = csrf_token

    # Ejecutar solo la petición correspondiente a este caso.
    if method == "post":
        response = client.post(url, data)
    else:
        response = client.get(url)

    assert response.status_code == expected_status

    if expected_status == 302:
        detail_url = reverse(
            "orders:detail",
            kwargs={"order_id": order.pk},
        )
        assert response["Location"] == (f"{reverse('users:login')}?next={detail_url}")

    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }
    assert after == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "extra_field", [None, "owner", "amount", "currency", "status", "unexpected"]
)
def test_payment_simulation_returns_same_404_for_foreing_and_missing_orders(
    client, settings, extra_field
):
    settings.DEBUG = False

    # Crear dos usuarios el cliente que hace la peticion y otro propietario
    owner = get_user_model().objects.create_user(
        username="detail-owner",
        password="ReliablePassword123!",
    )

    other_user = get_user_model().objects.create_user(
        username="detail-other-owner",
        password="ReliablePassword123!",
    )

    client.force_login(owner)

    # Crear un pedido pendiente que pertenezca a otro propietario
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

    # Elegir un identificador que no exista para el segundo caso
    missing_id = other_order.pk + 1
    assert not Order.objects.filter(pk=missing_id).exists()

    data = {
        "result": "approved",
        "idempotency_key": str(uuid4()),
    }
    if extra_field is not None:
        data[extra_field] = "manipulado"

    # Guardar el estado de los datos antes de consultar que comprobaremos despues
    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    responses = []

    for order_id in (other_order.pk, missing_id):
        url = reverse(
            "orders:simulate_payment",
            kwargs={"order_id": order_id},
        )

        response = client.post(url, data)

        after = {
            "orders": list(Order.objects.order_by("pk").values()),
            "order_items": list(OrderItem.objects.order_by("pk").values()),
            "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
            "carts": list(Cart.objects.order_by("pk").values()),
            "cart_items": list(CartItem.objects.order_by("pk").values()),
        }

        assert response.status_code == 404
        assert after == before

        html = response.content.decode()
        assert "Producto privado del otro cliente" not in html
        assert "PRIVADO-001" not in html
        assert "Licencia privada" not in html

        responses.append(response)

    assert responses[0].content == responses[1].content


@pytest.mark.django_db
def test_owner_can_approve_simulated_payment_for_pending_order(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="payment-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Pedido propio pendiente y su línea histórica.
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
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

    items_before = list(OrderItem.objects.filter(order=order).order_by("pk").values())
    payment_key = uuid4()

    # Actuar: solicitar la aprobación y seguir la redirección.
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
    order.refresh_from_db()

    assert order.status == Order.Status.PAID
    assert order.owner == owner
    assert order.total_amount == Decimal("12.90")
    assert order.currency == "EUR"

    # Crearse: exactamente un intento aprobado con los datos esperados.
    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == "approved"
    assert attempt.idempotency_key == payment_key
    assert attempt.amount == Decimal("12.90")
    assert attempt.currency == "EUR"
    assert attempt.created_at is not None

    # Conservarse: las líneas históricas permanecen intactas.
    items_after = list(OrderItem.objects.filter(order=order).order_by("pk").values())
    assert items_after == items_before

    # Mostrarse: resultado, estado y datos históricos en el detalle.
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


@pytest.mark.django_db
def test_payment_preserves_order_amount_and_currency_after_offer_changes(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="historical-payment-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Crear el pedido y su línea histórica desde una oferta de 12,90 EUR.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert order.total_amount == Decimal("12.90")
    assert order.currency == "EUR"
    assert OrderItem.objects.filter(order=order).count() == 1

    items_before = list(OrderItem.objects.filter(order=order).order_by("pk").values())

    # Cambiar la oferta del catálogo después de crear el pedido.
    offer.price = Decimal("19.90")
    offer.currency = "USD"
    offer.save(update_fields=["price", "currency"])

    offer.refresh_from_db()
    assert offer.price == Decimal("19.90")
    assert offer.currency == "USD"

    # Actuar: pagar el pedido pendiente original.
    response = client.post(
        reverse("orders:simulate_payment", kwargs={"order_id": order.pk}),
        {
            "result": "approved",
            "idempotency_key": str(uuid4()),
        },
    )

    # Comprobar: redirección y pedido pagado con sus valores originales.
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    order.refresh_from_db()

    assert order.status == Order.Status.PAID
    assert order.total_amount == Decimal("12.90")
    assert order.currency == "EUR"

    # El intento también utiliza los valores históricos del pedido.
    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert attempt.amount == Decimal("12.90")
    assert attempt.currency == "EUR"

    # La línea histórica permanece intacta.
    items_after = list(OrderItem.objects.filter(order=order).order_by("pk").values())
    assert items_after == items_before


@pytest.mark.django_db
def test_payment_preserves_cart_content_added_after_order_creation(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="payment-cart-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Pedido propio pendiente con una línea histórica.
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
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

    # Añadir contenido al carrito después de crear el pedido.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)

    assert CartItem.objects.filter(cart__owner=owner).count() == 1

    # Guardar todos los registros y valores del carrito y sus líneas.
    before = {
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    # Actuar: pagar el pedido pendiente.
    response = client.post(
        reverse("orders:simulate_payment", kwargs={"order_id": order.pk}),
        {
            "result": "approved",
            "idempotency_key": str(uuid4()),
        },
    )

    # Comprobar que el pago se ha completado.
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    # Volver a consultar el carrito y comprobar que permanece intacto.
    after = {
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    assert after == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "extra_field",
    ["owner", "amount", "currency", "status"],
)
def test_payment_rejects_extra_business_fields_without_changes(client, extra_field):
    # Preparar: usuario autenticado y otro usuario para intentar cambiar
    # deliberadamente el propietario enviado.
    owner = get_user_model().objects.create_user(
        username="payment-input-owner",
        password="ReliablePassword123!",
    )
    other_user = get_user_model().objects.create_user(
        username="payment-input-other",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Crear un pedido pendiente con su línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert not PaymentAttempt.objects.exists()

    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    # Campos que el cliente no tiene permitido enviar.
    manipulated_values = {
        "owner": str(other_user.pk),
        "amount": "0.01",
        "currency": "USD",
        "status": "paid",
    }

    data = {
        "result": "approved",
        "idempotency_key": str(uuid4()),
    }
    data[extra_field] = manipulated_values[extra_field]

    # Actuar: enviar una aprobación con un campo extra.
    response = client.post(
        reverse(
            "orders:simulate_payment",
            kwargs={"order_id": order.pk},
        ),
        data,
    )

    # Comprobar: rechazo y ausencia de cambios de negocio.
    assert response.status_code == 400

    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    assert after == before


@pytest.mark.django_db
def test_paid_order_rejects_new_payment_key_without_second_approval(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="payment-conflict-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Pedido pendiente con una línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1

    url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    first_key = uuid4()

    # Actuar: aprobar el primer pago.
    first_response = client.post(
        url,
        {
            "result": "approved",
            "idempotency_key": str(first_key),
        },
    )

    assert first_response.status_code == 302
    assert first_response["Location"] == reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert attempt.idempotency_key == first_key

    # Guardar el estado posterior al primer pago.
    before_retry = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }

    # Actuar: intentar pagar el mismo pedido con otra clave.
    second_key = uuid4()
    assert second_key != first_key

    second_response = client.post(
        url,
        {
            "result": "approved",
            "idempotency_key": str(second_key),
        },
    )

    # Comprobar: conflicto y conservación del primer pago.
    assert second_response.status_code == 409

    after_retry = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }

    assert after_retry == before_retry
    assert PaymentAttempt.objects.filter(order=order).count() == 1


@pytest.mark.django_db
def test_payment_replay_with_same_key_preserves_original_approval(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="payment-replay-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Pedido pendiente con una línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1

    url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    payment_key = uuid4()
    data = {
        "result": "approved",
        "idempotency_key": str(payment_key),
    }

    # Actuar: aprobar el primer pago.
    first_response = client.post(url, data)

    assert first_response.status_code == 302
    assert first_response["Location"] == detail_url

    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert attempt.idempotency_key == payment_key
    assert attempt.amount == order.total_amount
    assert attempt.currency == order.currency

    # Guardar el estado posterior al primer pago.
    before_retry = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }

    # Actuar: repetir el pago del mismo pedido con la misma clave.
    second_response = client.post(url, data)

    # Comprobar: misma redirección de éxito.
    assert second_response.status_code == 302
    assert second_response["Location"] == detail_url

    # El pedido y el intento original permanecen intactos.
    after_retry = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }

    assert after_retry == before_retry
    assert PaymentAttempt.objects.filter(order=order).count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("same_key", "expected_statuses"),
    [
        (True, [302, 302]),
        (False, [302, 409]),
    ],
)
def test_concurrent_payments_preserve_single_approval(same_key, expected_statuses):
    # Preparar: propietario y pedido pendiente con una línea.
    owner = get_user_model().objects.create_user(
        username="concurrent-payment-owner",
        password="ReliablePassword123!",
    )

    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.filter(order=order).exists()

    items_before = list(OrderItem.objects.filter(order=order).order_by("pk").values())

    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    first_key = uuid4()
    second_key = first_key if same_key else uuid4()

    # Los dos trabajadores esperan aquí antes de enviar sus POST.
    start = Barrier(2)

    def send_payment(payment_key):
        try:
            # Cada hilo tiene su propio cliente y conexión de Django.
            client = Client()
            client.force_login(owner)

            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend_pid = cursor.fetchone()[0]

                # Evitar esperas indefinidas ante un problema de bloqueo.
                cursor.execute("SET lock_timeout = '5s'")
                cursor.execute("SET statement_timeout = '10s'")

            start.wait(timeout=10)

            response = client.post(
                payment_url,
                {
                    "result": "approved",
                    "idempotency_key": str(payment_key),
                },
            )

            return {
                "status": response.status_code,
                "location": response.get("Location"),
                "key": payment_key,
                "backend_pid": backend_pid,
            }
        finally:
            # Cerrar las conexiones de este hilo.
            connections.close_all()

    # Actuar: lanzar ambos pagos concurrentemente.
    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(send_payment, first_key)
        second_future = executor.submit(send_payment, second_key)

        results = [
            first_future.result(timeout=30),
            second_future.result(timeout=30),
        ]

    # Comprobar que se utilizaron dos conexiones PostgreSQL distintas.
    assert len({result["backend_pid"] for result in results}) == 2

    # No presuponemos cuál de los dos POST termina primero.
    assert sorted(result["status"] for result in results) == expected_statuses

    successful_results = [result for result in results if result["status"] == 302]
    for result in successful_results:
        assert result["location"] == detail_url

    # Solo se ha persistido una aprobación.
    order.refresh_from_db()
    assert order.status == Order.Status.PAID
    assert order.total_amount == Decimal("12.90")
    assert order.currency == "EUR"

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert attempt.idempotency_key == successful_results[0]["key"]
    assert attempt.amount == Decimal("12.90")
    assert attempt.currency == "EUR"

    # Las líneas históricas permanecen intactas.
    items_after = list(OrderItem.objects.filter(order=order).order_by("pk").values())
    assert items_after == items_before


@pytest.mark.django_db
def test_payment_failure_rolls_back_attempt_and_preserves_cart(client, monkeypatch):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="payment-rollback-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Crear el pedido pendiente con su línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.filter(order=order).exists()

    # Preparar contenido en el carrito después de crear el pedido.
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    assert CartItem.objects.filter(cart__owner=owner).count() == 1

    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    # Provocar un fallo justo al intentar guardar el estado pagado.
    original_save = Order.save

    def fail_when_saving_paid_order(instance, *args, **kwargs):
        if instance.pk == order.pk and instance.status == Order.Status.PAID:
            # Confirmar que el intento ya se ha insertado en la transacción.
            assert (
                PaymentAttempt.objects.filter(
                    order=instance,
                    result=PaymentAttempt.Result.APPROVED,
                ).count()
                == 1
            )

            raise RuntimeError("Fallo técnico simulado al actualizar el pedido")

        return original_save(instance, *args, **kwargs)

    monkeypatch.setattr(Order, "save", fail_when_saving_paid_order)

    # Actuar: intentar pagar y comprobar que se produce el fallo previsto.
    url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )

    with pytest.raises(
        RuntimeError,
        match="Fallo técnico simulado al actualizar el pedido",
    ):
        client.post(
            url,
            {
                "result": "approved",
                "idempotency_key": str(uuid4()),
            },
        )

    # Comprobar: no quedan cambios parciales.
    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    assert after == before

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT
    assert not PaymentAttempt.objects.filter(order=order).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("invalid_field", "invalid_value"),
    [
        ("result", "inventado"),
        ("result", ""),
        ("result", None),
        ("idempotency_key", "no-es-un-uuid"),
        ("idempotency_key", ""),
        ("idempotency_key", None),
    ],
)
def test_payment_rejects_invalid_input_without_business_changes(
    client, settings, invalid_field, invalid_value
):
    settings.DEBUG = False

    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="invalid-payment-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Crear el pedido pendiente con su línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.exists()

    # Añadir contenido al carrito después de crear el pedido.
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    assert CartItem.objects.filter(cart__owner=owner).count() == 1

    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    # Partir de una entrada válida y alterar únicamente un campo.
    data = {
        "result": "approved",
        "idempotency_key": str(uuid4()),
    }

    if invalid_value is None:
        data.pop(invalid_field)
    else:
        data[invalid_field] = invalid_value

    # Actuar: solicitar el pago con esa entrada inválida.
    response = client.post(
        reverse(
            "orders:simulate_payment",
            kwargs={"order_id": order.pk},
        ),
        data,
    )

    # Comprobar: rechazo sin cambios de negocio.
    assert response.status_code == 400

    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    assert after == before

    # Comprobar que no se exponen detalles internos conocidos.
    content = response.content.decode()
    assert "Traceback" not in content
    assert "SECRET_KEY" not in content
    assert str(settings.BASE_DIR) not in content


@pytest.mark.django_db
def test_rejected_payment_records_failed_attempt_and_keeps_order_pending(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="rejected-payment-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Crear un pedido propio pendiente con una línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.owner == owner
    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.filter(order=order).exists()

    # Crear el pedido vacía el carrito: volver a añadir la oferta.
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    assert (
        CartItem.objects.filter(
            cart__owner=owner,
            offer=offer,
        ).count()
        == 1
    )

    expected_amount = order.total_amount
    expected_currency = order.currency
    payment_key = uuid4()

    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    # Actuar: solicitar el rechazo simulado y seguir la redirección.
    response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(payment_key),
        },
        follow=True,
    )

    # Comprobar: redirección al detalle del mismo pedido.
    assert response.redirect_chain == [(detail_url, 302)]
    assert response.status_code == 200

    # Se registra exactamente un intento fallido.
    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == "failed"
    assert attempt.idempotency_key == payment_key
    assert attempt.amount == expected_amount
    assert attempt.currency == expected_currency
    assert attempt.created_at is not None

    # El estado persistido del pedido sigue siendo pendiente.
    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT

    # El cliente recibe y ve un mensaje inequívoco de rechazo.
    visible_messages = [
        message.message for message in get_messages(response.wsgi_request)
    ]
    expected_message = "Pago simulado rechazado."

    assert expected_message in visible_messages
    assert "Pago simulado aprobado." not in visible_messages
    assertContains(response, expected_message)
    assertContains(response, "Estado: Pending payment")


@pytest.mark.django_db
def test_rejected_payment_preserves_cart_and_historical_order_items(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="rejected-payment-preservation-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Crear el pedido pendiente con una línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.owner == owner
    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.filter(order=order).exists()

    # La creación del pedido vacía el carrito.
    assert not CartItem.objects.filter(cart__owner=owner).exists()

    # Volver a preparar una selección en el carrito.
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    assert (
        CartItem.objects.filter(
            cart__owner=owner,
            offer=offer,
        ).count()
        == 1
    )

    # Guardar los datos persistidos antes del rechazo.
    before = {
        "cart": list(Cart.objects.filter(owner=owner).order_by("pk").values()),
        "cart_items": list(
            CartItem.objects.filter(cart__owner=owner).order_by("pk").values()
        ),
        "order_items": list(
            OrderItem.objects.filter(order=order).order_by("pk").values()
        ),
    }

    payment_key = uuid4()
    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    # Actuar: solicitar el rechazo simulado.
    response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(payment_key),
        },
    )

    # Comprobar que el rechazo se procesó y quedó registrado.
    assert response.status_code == 302
    assert response["Location"] == detail_url

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == "failed"
    assert attempt.idempotency_key == payment_key

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT

    # Volver a consultar la base de datos después del rechazo.
    after = {
        "cart": list(Cart.objects.filter(owner=owner).order_by("pk").values()),
        "cart_items": list(
            CartItem.objects.filter(cart__owner=owner).order_by("pk").values()
        ),
        "order_items": list(
            OrderItem.objects.filter(order=order).order_by("pk").values()
        ),
    }

    assert before == after


@pytest.mark.django_db
def test_rejected_payment_identical_repetition(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="rejected-payment-preservation-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Crear el pedido pendiente con una línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.owner == owner
    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.filter(order=order).exists()

    payment_key = uuid4()
    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    # Actuar: solicitar el rechazo simulado.
    response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(payment_key),
        },
    )

    # Comprobar que el rechazo se procesó y quedó registrado.
    assert response.status_code == 302
    assert response["Location"] == detail_url

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == "failed"
    assert attempt.idempotency_key == payment_key

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT

    # Guardar el estado después del primer rechazo.
    before = {
        "order": list(Order.objects.filter(pk=order.pk).values()),
        "attempts": list(
            PaymentAttempt.objects.filter(order=order).order_by("pk").values()
        ),
    }

    # Actuar: repetir exactamente la misma clave y resultado.
    repeated_response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(payment_key),
        },
        follow=True,
    )

    # Comprobar que vuelve al detalle y comunica el rechazo.
    assert repeated_response.redirect_chain == [(detail_url, 302)]
    assert repeated_response.status_code == 200
    assertContains(repeated_response, "Pago simulado rechazado.")

    # Comprobar que conserva el pedido y el intento originales.
    after = {
        "order": list(Order.objects.filter(pk=order.pk).values()),
        "attempts": list(
            PaymentAttempt.objects.filter(order=order).order_by("pk").values()
        ),
    }

    assert after == before
    assert PaymentAttempt.objects.filter(order=order).count() == 1


@pytest.mark.django_db
def test_rejected_payment_key_cannot_be_reused_for_approval(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="rejected-payment-preservation-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Crear el pedido pendiente con una línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.owner == owner
    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.filter(order=order).exists()

    # La creación del pedido vacía el carrito.
    assert not CartItem.objects.filter(cart__owner=owner).exists()

    # Volver a preparar una selección en el carrito.
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    assert (
        CartItem.objects.filter(
            cart__owner=owner,
            offer=offer,
        ).count()
        == 1
    )

    # Guardar los datos persistidos antes del rechazo.
    after = {
        "cart": list(Cart.objects.filter(owner=owner).order_by("pk").values()),
        "cart_items": list(
            CartItem.objects.filter(cart__owner=owner).order_by("pk").values()
        ),
        "order_items": list(
            OrderItem.objects.filter(order=order).order_by("pk").values()
        ),
    }

    # Preparar la clave del primer intento
    payment_key = uuid4()
    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    # Actuar: solicitar el rechazo simulado.
    response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(payment_key),
        },
    )

    # Comprobar que el rechazo se procesó y quedó registrado.
    assert response.status_code == 302
    assert response["Location"] == detail_url

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == "failed"
    assert attempt.idempotency_key == payment_key

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT

    # Guardar el pedido y sus intentos
    before = {
        "order": list(Order.objects.filter(pk=order.pk).values()),
        "attempts": list(
            PaymentAttempt.objects.filter(order=order).order_by("pk").values()
        ),
    }

    # Solicitar una aprobación con la misma clave
    response = client.post(
        payment_url,
        {
            "result": "approved",
            "idempotency_key": str(payment_key),
        },
    )

    # Comprobar el conflicto
    assert response.status_code == 409

    # Consultar de nuevo y comparar
    after = {
        "order": list(Order.objects.filter(pk=order.pk).values()),
        "attempts": list(
            PaymentAttempt.objects.filter(order=order).order_by("pk").values()
        ),
    }

    assert after == before

    # Expresar el resultado esperado
    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == "failed"
    assert attempt.idempotency_key == payment_key

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT


@pytest.mark.django_db
def test_approved_retry_with_new_key_preserves_failed_attempt(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="rejected-payment-preservation-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Crear el pedido pendiente con una línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.owner == owner
    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.filter(order=order).exists()

    # Preparar la clave del primer intento
    payment_key = uuid4()
    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    # Construye la dirección del detalle
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    # Actuar: solicitar el rechazo simulado.
    response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(payment_key),
        },
    )
    # Comprobar que el rechazo se procesó y quedó registrado.
    assert response.status_code == 302
    assert response["Location"] == detail_url

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == "failed"
    assert attempt.idempotency_key == payment_key

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT

    # Guardar el intento fallido para comprobar que permanece intacto.
    failed_attempt_pk = attempt.pk
    failed_attempt_before = PaymentAttempt.objects.values().get(pk=failed_attempt_pk)

    # Actuar: solicitar aprobación con una clave nueva.
    new_payment_key = uuid4()
    assert new_payment_key != payment_key

    response = client.post(
        payment_url,
        {
            "result": "approved",
            "idempotency_key": str(new_payment_key),
        },
        follow=True,
    )

    # Comprobar: redirección y mensaje de aprobación.
    assert response.redirect_chain == [(detail_url, 302)]
    assert response.status_code == 200
    assertContains(response, "Pago simulado aprobado.")

    # El mismo pedido pasa a pagado.
    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    # Existen exactamente dos intentos: un rechazo y una aprobación.
    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 2
    assert attempts.filter(result="failed").count() == 1
    assert attempts.filter(result="approved").count() == 1

    approved_attempt = attempts.get(result="approved")
    assert approved_attempt.idempotency_key == new_payment_key
    assert approved_attempt.amount == order.total_amount
    assert approved_attempt.currency == order.currency

    # El intento fallido original conserva todos sus datos.
    failed_attempt_after = PaymentAttempt.objects.values().get(pk=failed_attempt_pk)
    assert failed_attempt_after == failed_attempt_before


@pytest.mark.django_db
def test_order_detail_shows_only_own_payment_history_without_changes(client):
    # Preparar: dos propietarios y un pedido de cada uno.
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
        status=Order.Status.PAID,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )
    other_order = Order.objects.create(
        owner=other_user,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    first_attempt = PaymentAttempt.objects.create(
        order=own_order,
        idempotency_key=uuid4(),
        result=PaymentAttempt.Result.FAILED,
        amount=own_order.total_amount,
        currency=own_order.currency,
    )
    second_attempt = PaymentAttempt.objects.create(
        order=own_order,
        idempotency_key=uuid4(),
        result=PaymentAttempt.Result.APPROVED,
        amount=own_order.total_amount,
        currency=own_order.currency,
    )
    # El ID más alto recibe la fecha más antigua: ordenar solo por ID fallaría.
    older_attempt = PaymentAttempt.objects.create(
        order=own_order,
        idempotency_key=uuid4(),
        result=PaymentAttempt.Result.FAILED,
        amount=own_order.total_amount,
        currency=own_order.currency,
    )
    other_attempt = PaymentAttempt.objects.create(
        order=other_order,
        idempotency_key=uuid4(),
        result=PaymentAttempt.Result.FAILED,
        amount=other_order.total_amount,
        currency=other_order.currency,
    )

    recent_date = timezone.now().replace(microsecond=0)
    PaymentAttempt.objects.filter(pk__in=[first_attempt.pk, second_attempt.pk]).update(
        created_at=recent_date
    )
    PaymentAttempt.objects.filter(pk=older_attempt.pk).update(
        created_at=recent_date - timedelta(days=1)
    )

    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }

    # Actuar: consultar el historial propio, también disponible tras el pago.
    response = client.get(reverse("orders:detail", kwargs={"order_id": own_order.pk}))

    assert response.status_code == 200
    assertContains(response, "data-payment-attempt-id=", count=3)
    assertNotContains(response, f'data-payment-attempt-id="{other_attempt.pk}"')
    html = response.content.decode()
    displayed_ids = re.findall(r'data-payment-attempt-id="(\d+)"', html)
    assert displayed_ids == [
        str(second_attempt.pk),
        str(first_attempt.pk),
        str(older_attempt.pk),
    ]

    # Cada fila muestra su resultado y fecha, sin exponer la clave de pago.
    for attempt, label in (
        (second_attempt, "Aprobado"),
        (first_attempt, "Rechazado"),
        (older_attempt, "Rechazado"),
    ):
        attempt.refresh_from_db()
        row = re.search(
            rf'<li data-payment-attempt-id="{attempt.pk}">(.*?)</li>',
            html,
            flags=re.DOTALL,
        )
        assert row is not None
        row_text = " ".join(row.group(1).split())
        assert f"Resultado: {label}" in row_text
        local_date = timezone.localtime(attempt.created_at)
        assert local_date.strftime("%d/%m/%Y %H:%M") in row_text
        assert f'datetime="{local_date.isoformat()}"' in row_text
        assertNotContains(response, str(attempt.idempotency_key))

    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }
    assert after == before


@pytest.mark.django_db
def test_order_detail_query_count_does_not_grow_with_payment_attempts(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="payment-history-query-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    query_counts = []

    for attempt_count in (1, 10):
        # Preparar cada escenario fuera de la medición.
        order = Order.objects.create(
            owner=owner,
            status=Order.Status.PENDING_PAYMENT,
            total_amount=Decimal("12.90"),
            currency="EUR",
        )

        # Mantener una línea histórica en ambos escenarios.
        OrderItem.objects.create(
            order=order,
            product_sku="HISTORY-001",
            product_name="Producto histórico",
            license_name="Licencia comercial",
            terms_version="1.0",
            price=Decimal("12.90"),
            currency="EUR",
        )

        attempts = []
        for _ in range(attempt_count):
            attempt = PaymentAttempt.objects.create(
                order=order,
                idempotency_key=uuid4(),
                result=PaymentAttempt.Result.FAILED,
                amount=order.total_amount,
                currency=order.currency,
            )
            attempts.append(attempt)

        detail_url = reverse(
            "orders:detail",
            kwargs={"order_id": order.pk},
        )

        # Actuar: medir únicamente la consulta y el renderizado del detalle.
        with CaptureQueriesContext(connection) as queries:
            response = client.get(detail_url)

        query_counts.append(len(queries))

        # Comprobar que el historial se muestra realmente.
        assert response.status_code == 200
        assertContains(
            response,
            "data-payment-attempt-id=",
            count=attempt_count,
        )

        for attempt in attempts:
            assertContains(
                response,
                f'data-payment-attempt-id="{attempt.pk}"',
                count=1,
            )

    # Un intento y diez intentos requieren las mismas consultas.
    assert query_counts[0] == query_counts[1], query_counts

    # Presupuesto actual del detalle, incluido el historial.
    assert max(query_counts) <= 5, query_counts


@pytest.mark.django_db
def test_paid_order_rejects_new_attempts_and_preserves_replayed_results(client):
    # Preparar: aprobar el primer pago para dejar el pedido pagado.
    # Usuario autenticado
    owner = get_user_model().objects.create_user(
        username="payment-conflict-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Pedido pendiente con una línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1

    url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    first_key = uuid4()

    # Actuar: aprobar el primer pago.
    first_response = client.post(
        url,
        {
            "result": "approved",
            "idempotency_key": str(first_key),
        },
    )

    assert first_response.status_code == 302
    assert first_response["Location"] == reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert attempt.idempotency_key == first_key

    # Preparar la clave del segundo intento
    payment_key = uuid4()
    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )

    before = {
        "order": list(Order.objects.filter(pk=order.pk).values()),
        "attempts": list(
            PaymentAttempt.objects.filter(order=order).order_by("pk").values()
        ),
    }

    # Actuar: solicitar el rechazo simulado.
    second_response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(payment_key),
        },
    )
    # Comprobar que se rechaza el nuevo intento sin registrarlo.
    assert second_response.status_code == 409

    # El intento original conserva su resultado y su clave.
    attempt.refresh_from_db()
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert attempt.idempotency_key == first_key

    # El pedido sigue pagado y no se añade otro intento.
    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    # Comprobar que no se creo otro intento.
    assert PaymentAttempt.objects.filter(order=order).count() == 1

    after = {
        "order": list(Order.objects.filter(pk=order.pk).values()),
        "attempts": list(
            PaymentAttempt.objects.filter(order=order).order_by("pk").values()
        ),
    }

    assert after == before


@pytest.mark.django_db
def test_paid_order_rejects_failed_attempt_with_new_key_without_changes(client):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="payment-conflict-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    # Pedido pendiente con una línea histórica.
    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1

    url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    first_key = uuid4()

    # Actuar: aprobar el primer pago.
    first_response = client.post(
        url,
        {
            "result": "approved",
            "idempotency_key": str(first_key),
        },
    )

    assert first_response.status_code == 302
    assert first_response["Location"] == reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert attempt.idempotency_key == first_key

    # Guardar el estado posterior al primer pago.
    before_retry = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }

    # Actuar: intentar pagar el mismo pedido con otra clave.
    second_key = uuid4()
    assert second_key != first_key

    second_response = client.post(
        url,
        {
            "result": "failed",
            "idempotency_key": str(second_key),
        },
    )

    # Comprobar: conflicto y conservación del primer pago.
    assert second_response.status_code == 409

    after_retry = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
    }

    assert after_retry == before_retry
    assert PaymentAttempt.objects.filter(order=order).count() == 1


@pytest.mark.django_db
def test_failed_payment_replay_preserves_paid_order_and_attempts(client):
    # Preparar: usuario autenticado y pedido pendiente.
    owner = get_user_model().objects.create_user(
        username="failed-replay-paid-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1

    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    # Preparar: registrar el primer intento rechazado.
    failed_key = uuid4()
    failed_response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(failed_key),
        },
        follow=True,
    )

    assert failed_response.redirect_chain == [(detail_url, 302)]
    assert failed_response.status_code == 200

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    failed_attempt = attempts.get()
    assert failed_attempt.result == PaymentAttempt.Result.FAILED
    assert failed_attempt.idempotency_key == failed_key

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT

    # Preparar: aprobar con otra clave para dejar el pedido pagado.
    approved_key = uuid4()
    assert approved_key != failed_key

    approved_response = client.post(
        payment_url,
        {
            "result": "approved",
            "idempotency_key": str(approved_key),
        },
        follow=True,
    )

    assert approved_response.redirect_chain == [(detail_url, 302)]
    assert approved_response.status_code == 200

    order.refresh_from_db()
    assert order.status == Order.Status.PAID
    assert attempts.count() == 2

    approved_attempt = attempts.get(result=PaymentAttempt.Result.APPROVED)
    assert approved_attempt.idempotency_key == approved_key

    # Guardar el estado del pedido pagado y de todo su historial.
    before = {
        "order": list(Order.objects.filter(pk=order.pk).values()),
        "order_items": list(
            OrderItem.objects.filter(order=order).order_by("pk").values()
        ),
        "attempts": list(
            PaymentAttempt.objects.filter(order=order).order_by("pk").values()
        ),
    }

    # Actuar: repetir la clave y el resultado del rechazo original.
    response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(failed_key),
        },
        follow=True,
    )

    # Comprobar: devuelve el rechazo histórico, sin conflicto.
    assert response.redirect_chain == [(detail_url, 302)]
    assert response.status_code == 200
    assertContains(response, "Pago simulado rechazado.")

    visible_messages = [
        message.message for message in get_messages(response.wsgi_request)
    ]
    assert "Pago simulado rechazado." in visible_messages
    assert "Pago simulado aprobado." not in visible_messages

    # El pedido sigue pagado y el intento original sigue rechazado.
    order.refresh_from_db()
    failed_attempt.refresh_from_db()

    assert order.status == Order.Status.PAID
    assert failed_attempt.result == PaymentAttempt.Result.FAILED
    assert failed_attempt.idempotency_key == failed_key
    assert attempts.count() == 2

    # La repetición no modifica ningún dato ni añade intentos.
    after = {
        "order": list(Order.objects.filter(pk=order.pk).values()),
        "order_items": list(
            OrderItem.objects.filter(order=order).order_by("pk").values()
        ),
        "attempts": list(
            PaymentAttempt.objects.filter(order=order).order_by("pk").values()
        ),
    }

    assert after == before


@pytest.mark.django_db
def test_anonymous_payment_rejection_redirects_to_login_without_changes():
    # Preparar: pedido existente de un usuario.
    owner = get_user_model().objects.create_user(
        username="anonymous-payment-order-owner",
        password="ReliablePassword123!",
    )

    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    # Cliente anónimo con comprobación real de CSRF.
    client = Client(enforce_csrf_checks=True)

    login_url = reverse("users:login")

    # Abrir el formulario de login obtiene el token, sin iniciar sesión.
    login_response = client.get(login_url)
    assert login_response.status_code == 200
    csrf_token = client.cookies["csrftoken"].value

    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    # Actuar: solicitar un rechazo sin estar autenticado, con CSRF válido.
    response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(uuid4()),
            "csrfmiddlewaretoken": csrf_token,
        },
    )

    # Comprobar: redirección al login con destino posterior al detalle.
    assert response.status_code == 302
    assert response["Location"] == f"{login_url}?next={detail_url}"

    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    assert after == before


@pytest.mark.django_db
def test_payment_rejection_without_csrf_returns_403_without_changes():
    # Preparar: usuario y pedido propio pendiente.
    owner = get_user_model().objects.create_user(
        username="missing-csrf-payment-owner",
        password="ReliablePassword123!",
    )

    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.filter(order=order).exists()

    # Autenticar al cliente y activar la comprobación real de CSRF.
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)

    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )

    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    # Actuar: solicitar el rechazo sin enviar un token CSRF.
    response = client.post(
        payment_url,
        {
            "result": "failed",
            "idempotency_key": str(uuid4()),
        },
    )

    # Comprobar: acceso prohibido por falta de CSRF.
    assert response.status_code == 403

    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    assert after == before


@pytest.mark.django_db
def test_payment_rejection_returns_same_404_for_foreign_and_missing_orders(settings):
    settings.DEBUG = False

    # Preparar: usuario solicitante y propietario del pedido ajeno.
    owner = get_user_model().objects.create_user(
        username="payment-requesting-user",
        password="ReliablePassword123!",
    )
    other_user = get_user_model().objects.create_user(
        username="payment-other-owner",
        password="ReliablePassword123!",
    )

    offer = create_available_offer()
    add_offer_to_cart(owner=other_user, offer_id=offer.pk)
    other_order = create_order_from_cart(owner=other_user)

    assert other_order.owner == other_user
    assert other_order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=other_order).count() == 1

    # Obtener el token CSRF mientras el cliente todavía es anónimo.
    client = Client(enforce_csrf_checks=True)
    login_response = client.get(reverse("users:login"))

    assert login_response.status_code == 200
    csrf_token = client.cookies["csrftoken"].value

    # Autenticar después al usuario que no es propietario.
    client.force_login(owner)

    # Preparar un identificador que no corresponde a ningún pedido.
    missing_id = other_order.pk + 1
    assert not Order.objects.filter(pk=missing_id).exists()

    foreign_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": other_order.pk},
    )
    missing_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": missing_id},
    )

    # Guardar los datos antes de las peticiones.
    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    data = {
        "result": "failed",
        "idempotency_key": str(uuid4()),
        "csrfmiddlewaretoken": csrf_token,
    }

    # Actuar: solicitar el rechazo sobre un pedido ajeno y otro inexistente.
    foreign_response = client.post(foreign_url, data)
    missing_response = client.post(missing_url, data)

    # Comprobar: mismo estado y contenido, sin revelar si el pedido existe.
    assert foreign_response.status_code == 404
    assert missing_response.status_code == 404
    assert foreign_response.content == missing_response.content

    # Comprobar que ninguna petición ha cambiado los datos.
    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    assert after == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("scenario", "expected_status"),
    [
        ("anonymous", 302),
        ("missing_csrf", 403),
        ("invalid_csrf", 403),
        ("foreign_order", 404),
        ("missing_order", 404),
    ],
)
def test_payment_retry_enforces_security_without_changes(
    settings, scenario, expected_status
):
    settings.DEBUG = False

    # Preparar: usuario solicitante y otro usuario.
    owner = get_user_model().objects.create_user(
        username="retry-requesting-user",
        password="ReliablePassword123!",
    )
    other_user = get_user_model().objects.create_user(
        username="retry-other-owner",
        password="ReliablePassword123!",
    )

    # En el escenario de pedido ajeno, pertenece al otro usuario.
    order_owner = other_user if scenario == "foreign_order" else owner

    offer = create_available_offer()
    add_offer_to_cart(owner=order_owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=order_owner)

    # Preparar un rechazo previo: el pedido sigue pendiente.
    failed_attempt = PaymentAttempt.objects.create(
        order=order,
        idempotency_key=uuid4(),
        result=PaymentAttempt.Result.FAILED,
        amount=order.total_amount,
        currency=order.currency,
    )

    assert order.status == Order.Status.PENDING_PAYMENT

    client = Client(enforce_csrf_checks=True)

    # Obtener una cookie CSRF válida antes de preparar cada escenario.
    login_url = reverse("users:login")
    login_response = client.get(login_url)
    assert login_response.status_code == 200
    csrf_token = client.cookies["csrftoken"].value

    if scenario != "anonymous":
        client.force_login(owner)

    target_id = order.pk
    if scenario == "missing_order":
        target_id = order.pk + 1
        assert not Order.objects.filter(pk=target_id).exists()

    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": target_id},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": target_id},
    )

    new_key = uuid4()
    assert new_key != failed_attempt.idempotency_key

    data = {
        "result": "approved",
        "idempotency_key": str(new_key),
        "csrfmiddlewaretoken": csrf_token,
    }

    if scenario == "missing_csrf":
        data.pop("csrfmiddlewaretoken")
    elif scenario == "invalid_csrf":
        # Alterar el token enviado, conservando la cookie válida.
        replacement = "A" if csrf_token[0] != "A" else "B"
        data["csrfmiddlewaretoken"] = replacement + csrf_token[1:]

    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    # Actuar: intentar aprobar con una clave nueva.
    response = client.post(payment_url, data)

    # Comprobar la respuesta de seguridad correspondiente.
    assert response.status_code == expected_status

    if scenario == "anonymous":
        assert response["Location"] == f"{login_url}?next={detail_url}"

    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }

    assert after == before

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT
    assert PaymentAttempt.objects.filter(order=order).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_rejection_and_approval_preserve_paid_order():
    # Preparar: propietario y pedido pendiente con una línea histórica.
    owner = get_user_model().objects.create_user(
        username="concurrent-rejection-approval-owner",
        password="ReliablePassword123!",
    )

    offer = create_available_offer()
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    assert order.status == Order.Status.PENDING_PAYMENT
    assert OrderItem.objects.filter(order=order).count() == 1
    assert not PaymentAttempt.objects.filter(order=order).exists()

    items_before = list(OrderItem.objects.filter(order=order).order_by("pk").values())
    expected_amount = order.total_amount
    expected_currency = order.currency

    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )

    failed_key = uuid4()
    approved_key = uuid4()
    assert failed_key != approved_key

    # Ambos trabajadores esperan aquí antes de enviar sus peticiones.
    start = Barrier(2)

    def send_payment(result, payment_key):
        try:
            # Cada hilo utiliza su propio cliente y conexión.
            client = Client()
            client.force_login(owner)

            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend_pid = cursor.fetchone()[0]

                # Limitar las esperas si aparece un problema de bloqueo.
                cursor.execute("SET lock_timeout = '5s'")
                cursor.execute("SET statement_timeout = '10s'")

            start.wait(timeout=10)

            response = client.post(
                payment_url,
                {
                    "result": result,
                    "idempotency_key": str(payment_key),
                },
            )

            return {
                "status": response.status_code,
                "location": response.get("Location"),
                "backend_pid": backend_pid,
            }
        finally:
            connections.close_all()

    # Actuar: lanzar un rechazo y una aprobación concurrentemente.
    with ThreadPoolExecutor(max_workers=2) as executor:
        failed_future = executor.submit(
            send_payment,
            "failed",
            failed_key,
        )
        approved_future = executor.submit(
            send_payment,
            "approved",
            approved_key,
        )

        failed_response = failed_future.result(timeout=30)
        approved_response = approved_future.result(timeout=30)

    # Comprobar que participaron dos conexiones PostgreSQL distintas.
    assert failed_response["backend_pid"] != approved_response["backend_pid"]

    # La aprobación debe completarse en cualquiera de los dos órdenes.
    assert approved_response["status"] == 302
    assert approved_response["location"] == detail_url

    # El rechazo depende de cuál de las dos operaciones se procesó primero.
    assert failed_response["status"] in (302, 409)

    # El pedido termina pagado y conserva sus datos históricos.
    order.refresh_from_db()
    assert order.status == Order.Status.PAID
    assert order.owner == owner
    assert order.total_amount == expected_amount
    assert order.currency == expected_currency

    attempts = PaymentAttempt.objects.filter(order=order)

    # Existe exactamente una aprobación con la clave enviada.
    assert attempts.filter(result=PaymentAttempt.Result.APPROVED).count() == 1

    approved_attempt = attempts.get(result=PaymentAttempt.Result.APPROVED)
    assert approved_attempt.idempotency_key == approved_key

    if failed_response["status"] == 302:
        # El rechazo se procesó antes de que el pedido quedara pagado.
        assert failed_response["location"] == detail_url
        assert attempts.count() == 2
        assert attempts.filter(result=PaymentAttempt.Result.FAILED).count() == 1

        failed_attempt = attempts.get(result=PaymentAttempt.Result.FAILED)
        assert failed_attempt.idempotency_key == failed_key
    else:
        # La aprobación se procesó primero: no se registra el rechazo.
        assert attempts.count() == 1
        assert not attempts.filter(result=PaymentAttempt.Result.FAILED).exists()
        assert not attempts.filter(idempotency_key=failed_key).exists()

    # Todos los intentos registrados usan el importe y moneda del pedido.
    for attempt in attempts:
        assert attempt.amount == expected_amount
        assert attempt.currency == expected_currency

    items_after = list(OrderItem.objects.filter(order=order).order_by("pk").values())
    assert items_after == items_before
