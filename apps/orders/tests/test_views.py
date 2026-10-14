import re
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier
from typing import cast
from uuid import UUID, uuid4

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.db import connection, connections
from django.http import HttpResponse
from django.template.defaultfilters import date as format_date
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains

from apps.cart.models import Cart, CartItem
from apps.cart.services import add_offer_to_cart
from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer
from apps.orders.models import LicenseGrant, Order, OrderItem, PaymentAttempt
from apps.orders.services import approve_simulated_payment, create_order_from_cart


def create_available_offer(
    *,
    terms_text="Condiciones completas de prueba.",
    usage_scope="Uso de prueba web",
):
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
        usage_scope=usage_scope,
        summary="Resumen de licencia de prueba web.",
        terms_version="1.0",
        terms_text=terms_text,
    )
    return ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
        grantor_name="Concedente de prueba",
        rights_holder_name="Titular de prueba",
    )


def create_payable_order_item(
    *,
    order,
    product_name,
    product_sku,
    license_name,
    terms_version,
    price,
    currency,
):
    identifier = uuid4().hex
    terms_text = "Condiciones completas de la compra de prueba."
    usage_scope = "Proyectos audiovisuales"

    category, _ = Category.objects.get_or_create(
        slug="pagos-de-prueba",
        defaults={"name": "Pagos de prueba"},
    )
    product = Product.objects.create(
        category=category,
        name=product_name,
        slug=f"producto-{identifier}",
        sku=product_sku,
        summary="Producto de prueba.",
        description="Producto para comprobar el pago.",
        duration_ms=1000,
        audio_format="wav",
        sample_rate_hz=48000,
        bit_depth=24,
    )
    license_type, _ = LicenseType.objects.get_or_create(
        name=license_name,
        defaults={
            "slug": f"licencia-{identifier}",
            "usage_scope": usage_scope,
            "summary": "Licencia para comprobar el pago.",
            "terms_version": terms_version,
            "terms_text": terms_text,
        },
    )

    return OrderItem.objects.create(
        order=order,
        source_product=product,
        source_license_type=license_type,
        product_name=product_name,
        product_sku=product_sku,
        license_name=license_name,
        terms_version=terms_version,
        terms_text=terms_text,
        usage_scope=usage_scope,
        grantor_name="Concedente de prueba",
        rights_holder_name="Titular de prueba",
        price=price,
        currency=currency,
    )


@pytest.fixture
def documented_purchase(db):
    # Preparar: propietario y oferta con condiciones documentadas.
    owner = get_user_model().objects.create_user(
        username="documented-license-owner",
    )
    offer = create_available_offer(
        terms_text=(
            "Permite incorporar el sonido en proyectos audiovisuales comerciales. "
            "La autorización es mundial, no exclusiva y de duración indefinida. "
            "No permite revender el sonido como archivo independiente."
        ),
        usage_scope="Proyectos audiovisuales comerciales",
    )
    license_type = offer.license_type

    license_type.terms_text = (
        "Permite incorporar el sonido en proyectos audiovisuales comerciales. "
        "La autorización es mundial, no exclusiva y de duración indefinida. "
        "No permite revender el sonido como archivo independiente."
    )
    license_type.usage_scope = "Proyectos audiovisuales comerciales"
    license_type.save(update_fields=["terms_text", "usage_scope"])

    offer.grantor_name = "Distribuidora de prueba"
    offer.rights_holder_name = "Estudio titular de prueba"
    offer.save(update_fields=["grantor_name", "rights_holder_name"])

    # Conservar los valores originales del catálogo como resultado esperado.
    expected = {
        "product_name": offer.product.name,
        "product_sku": offer.product.sku,
        "license_name": license_type.name,
        "terms_version": license_type.terms_version,
        "terms_text": license_type.terms_text,
        "usage_scope": license_type.usage_scope,
        "grantor_name": offer.grantor_name,
        "rights_holder_name": offer.rights_holder_name,
    }

    # Preparar: compra y permiso mediante los servicios existentes.
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    order = create_order_from_cart(owner=owner)

    approve_simulated_payment(
        owner=owner,
        order_id=order.pk,
        result=PaymentAttempt.Result.APPROVED,
        idempotency_key=uuid4(),
    )

    grant = LicenseGrant.objects.get(order_item__order=order)

    return owner, offer, grant, expected


@pytest.fixture
def prepared_purchase_offer(db):
    # Prepara:un usuario y una oferta con condiciones completas todavía sin comprar.
    owner = get_user_model().objects.create_user(
        username="rf10-prepared-owner",
    )
    offer = create_available_offer(
        terms_text="Condiciones originales completas.",
    )

    offer.grantor_name = "Concedente original"
    offer.rights_holder_name = "Titular original"
    offer.save(update_fields=["grantor_name", "rights_holder_name"])

    return owner, offer


def capture_purchase_business_data():
    # Copiar registros y valores para detectar altas, bajas y modificaciones.
    return {
        "orders": list(Order.objects.order_by("pk").values()),
        "items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "grants": list(LicenseGrant.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
    }


def prepare_pending_order(owner, offer):
    add_offer_to_cart(owner=owner, offer_id=offer.pk)
    return create_order_from_cart(owner=owner)


def request_payment_approval(client, order, payment_key=None):
    return client.post(
        reverse(
            "orders:simulate_payment",
            kwargs={"order_id": order.pk},
        ),
        {
            "result": PaymentAttempt.Result.APPROVED,
            "idempotency_key": str(payment_key or uuid4()),
        },
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
    settings.DEBUG = (
        False  # desactiva el modo de depuración de Django durante la prueba.
    )

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

    create_payable_order_item(
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
    order.refresh_from_db(from_queryset=None)

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

    offer.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)

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

    create_payable_order_item(
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

    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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
    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
    assert order.status == Order.Status.PENDING_PAYMENT
    assert not PaymentAttempt.objects.filter(order=order).exists()


@pytest.mark.django_db
def test_license_issue_failure_rolls_back_payment_order_and_grants(client, monkeypatch):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="license-rollback-owner",
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

    for name, sku, price in [
        ("Impacto cinematográfico", "PED-001", "12.90"),
        ("Pasos sobre madera", "PED-002", "8.50"),
    ]:
        create_payable_order_item(
            order=order,
            product_name=name,
            product_sku=sku,
            license_name="Licencia comercial",
            terms_version="1.0",
            price=Decimal(price),
            currency="EUR",
        )

    # Preparar: conservar los datos anteriores a la aprobación.
    order_before = Order.objects.filter(pk=order.pk).values().get()
    items_before = list(OrderItem.objects.filter(order=order).order_by("pk").values())
    assert not PaymentAttempt.objects.filter(order=order).exists()
    assert not LicenseGrant.objects.filter(order_item__order=order).exists()

    # Preparar: permitir el primer permiso y fallar al guardar el segundo.
    original_save = LicenseGrant.save
    emission_count = 0

    def fail_on_second_grant(instance, *args, **kwargs):
        nonlocal emission_count
        emission_count += 1

        if emission_count == 2:
            # Confirmar que ya existen cambios que deben revertirse.
            assert LicenseGrant.objects.filter(order_item__order=order).count() == 1
            assert (
                PaymentAttempt.objects.filter(
                    order=order,
                    result=PaymentAttempt.Result.APPROVED,
                ).count()
                == 1
            )
            assert Order.objects.get(pk=order.pk).status == Order.Status.PAID

            raise RuntimeError("Fallo simulado al emitir el segundo permiso")

        return original_save(instance, *args, **kwargs)

    monkeypatch.setattr(LicenseGrant, "save", fail_on_second_grant)

    # Actuar: solicitar la aprobación y provocar el fallo de emisión.
    with pytest.raises(
        RuntimeError,
        match="Fallo simulado al emitir el segundo permiso",
    ):
        client.post(
            reverse(
                "orders:simulate_payment",
                kwargs={"order_id": order.pk},
            ),
            {
                "result": PaymentAttempt.Result.APPROVED,
                "idempotency_key": str(uuid4()),
            },
        )

    # Comprobar: se alcanzó la segunda emisión.
    assert emission_count == 2

    # Comprobar: el pedido recupera todos sus valores anteriores.
    order_after = Order.objects.filter(pk=order.pk).values().get()
    assert order_after == order_before

    order.refresh_from_db(from_queryset=None)
    assert order.status == Order.Status.PENDING_PAYMENT

    # Comprobar: el intento aprobado y el primer permiso se deshicieron.
    assert not PaymentAttempt.objects.filter(order=order).exists()
    assert not LicenseGrant.objects.filter(order_item__order=order).exists()

    # Comprobar: las líneas históricas permanecen intactas.
    items_after = list(OrderItem.objects.filter(order=order).order_by("pk").values())
    assert items_after == items_before


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
    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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
    order.refresh_from_db(from_queryset=None)
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
        attempt.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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
    attempt.refresh_from_db(from_queryset=None)
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert attempt.idempotency_key == first_key

    # El pedido sigue pagado y no se añade otro intento.
    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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

    order.refresh_from_db(from_queryset=None)
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
    order.refresh_from_db(from_queryset=None)
    failed_attempt.refresh_from_db(from_queryset=None)

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

    order.refresh_from_db(from_queryset=None)
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
    order.refresh_from_db(from_queryset=None)
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payment_result",
    [None, PaymentAttempt.Result.FAILED],
    ids=["pending_without_attempts", "failed_payment"],
)
def test_license_list_excludes_unpaid_order_items(client, payment_result):
    # Preparar: usuario autenticado
    owner = get_user_model().objects.create_user(
        username="paid_order", password="ReliablePassword123!"
    )
    client.force_login(owner)

    # Preparar: primer pedido (aprobar el pago de la compra de control)
    paid_order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    create_payable_order_item(
        order=paid_order,
        product_name="Impacto cinematográfico",
        product_sku="PED-001",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )

    # Actuar: solicitar la aprobación y seguir la redirección.
    payment_key = uuid4()

    payment_url = reverse(
        "orders:simulate_payment",
        kwargs={"order_id": paid_order.pk},
    )
    detail_url = reverse(
        "orders:detail",
        kwargs={"order_id": paid_order.pk},
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
    paid_order.refresh_from_db(from_queryset=None)

    assert paid_order.status == Order.Status.PAID
    assert paid_order.owner == owner
    assert paid_order.total_amount == Decimal("12.90")
    assert paid_order.currency == "EUR"

    # Preparar el derecho que deberá aparecer en «Mis licencias».
    paid_grant = LicenseGrant.objects.get(order_item__order=paid_order)

    # Comprobar: la existencia de su derecho activo.
    assert paid_grant.status == LicenseGrant.Status.ACTIVE

    # Preparar: un segundo pedido (ejecutar rechazo cuando corresponda)
    unpaid_order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("5.90"),
        currency="EUR",
    )

    OrderItem.objects.create(
        order=unpaid_order,
        product_name="Reverd Water",
        product_sku="PED-002",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("5.90"),
        currency="EUR",
    )

    # Preparar: registrar un rechazo solo en el caso parametrizado correspondiente.
    if payment_result is not None:
        rejected_response = client.post(
            reverse(
                "orders:simulate_payment",
                kwargs={"order_id": unpaid_order.pk},
            ),
            {
                "result": payment_result,
                "idempotency_key": str(uuid4()),
            },
        )

        assert rejected_response.status_code == 302

        failed_attempt = PaymentAttempt.objects.get(order=unpaid_order)
        assert failed_attempt.result == PaymentAttempt.Result.FAILED

    else:
        assert not PaymentAttempt.objects.filter(order=unpaid_order).exists()

    # Comprobar: en ambos casos el segundo pedido sigue pendiente.
    unpaid_order.refresh_from_db(from_queryset=None)
    assert unpaid_order.status == Order.Status.PENDING_PAYMENT

    # Actuar: consultar las licencias del usuario autenticado.
    response = client.get("/licenses/")

    # Comprobar: la sección se puede consultar.
    assert response.status_code == 200

    # Comprobar: aparece la compra pagada de control.
    assertContains(response, "Impacto cinematográfico")
    assertContains(response, "PED-001")

    # Comprobar: no aparece la línea del pedido pendiente.
    assertNotContains(response, "Reverd Water")
    assertNotContains(response, "PED-002")

    # Comprobar: no existen derechos para el pedido pendiente.
    assert not LicenseGrant.objects.filter(
        order_item__order=unpaid_order,
    ).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("same_key", "expected_statuses"),
    [
        (True, [302, 302]),
        (False, [302, 409]),
    ],
    ids=["same_payment_key", "different_payment_keys"],
)
def test_concurrent_approvals_issue_exactly_one_grant_per_order_item(
    same_key, expected_statuses
):
    # Preparar: propietario y pedido pendiente.
    owner = get_user_model().objects.create_user(
        username="concurrent-license-owner",
        password="ReliablePassword123!",
    )
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("21.40"),
        currency="EUR",
    )

    # Preparar: dos líneas históricas que deberán recibir un permiso cada una.
    for name, sku, price in [
        ("Impacto cinematográfico", "PED-001", "12.90"),
        ("Pasos sobre madera", "PED-002", "8.50"),
    ]:
        create_payable_order_item(
            order=order,
            product_name=name,
            product_sku=sku,
            license_name="Licencia comercial",
            terms_version="1.0",
            price=Decimal(price),
            currency="EUR",
        )

    expected_item_ids = set(
        OrderItem.objects.filter(order=order).values_list("pk", flat=True)
    )
    assert not PaymentAttempt.objects.filter(order=order).exists()
    assert not LicenseGrant.objects.filter(order_item__order=order).exists()

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
    start = Barrier(2)

    # Preparar: cada hilo utiliza su propio cliente autenticado y conexión.
    def send_approval(payment_key):
        try:
            thread_client = Client()
            thread_client.force_login(owner)

            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend_pid = cursor.fetchone()[0]

                # Limitar las esperas si se produce un problema de bloqueo.
                cursor.execute("SET lock_timeout = '5s'")
                cursor.execute("SET statement_timeout = '10s'")

            # Esperar a que ambos trabajadores estén preparados.
            start.wait(timeout=10)

            response = thread_client.post(
                payment_url,
                {
                    "result": PaymentAttempt.Result.APPROVED,
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
            connections.close_all()

    # Actuar: enviar las dos solicitudes de aprobación concurrentemente.
    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(send_approval, first_key)
        second_future = executor.submit(send_approval, second_key)

        results = [
            first_future.result(timeout=30),
            second_future.result(timeout=30),
        ]

    # Comprobar: las solicitudes utilizaron conexiones PostgreSQL distintas.
    assert len({result["backend_pid"] for result in results}) == 2

    # Comprobar: respuestas esperadas sin depender del orden de finalización.
    assert sorted(result["status"] for result in results) == expected_statuses

    successful_results = [result for result in results if result["status"] == 302]
    for result in successful_results:
        assert result["location"] == detail_url

    # Comprobar: el pedido queda pagado con un único intento aprobado.
    order.refresh_from_db(from_queryset=None)
    assert order.status == Order.Status.PAID

    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert attempt.idempotency_key == successful_results[0]["key"]

    # Comprobar: hay exactamente dos permisos, uno por cada línea original.
    grants = list(
        LicenseGrant.objects.filter(order_item__order=order)
        .select_related("order_item__order__owner")
        .order_by("pk")
    )

    assert len(grants) == 2
    assert {grant.order_item.pk for grant in grants} == expected_item_ids

    # Comprobar: ambos permisos están activos y pertenecen al propietario.
    for grant in grants:
        assert grant.status == LicenseGrant.Status.ACTIVE
        assert grant.order_item.order.owner.pk == owner.pk
        assert grant.issued_at is not None


@pytest.mark.django_db
def test_authenticated_user_without_grants_sees_empty_license_list(client):
    # Preparar: usuario autenticado sin permisos de uso.
    owner = get_user_model().objects.create_user(
        username="empty-license-owner",
        password="ReliablePassword123!",
    )
    client.force_login(owner)

    assert not LicenseGrant.objects.exists()

    # Actuar: consultar «Mis licencias».
    response = client.get("/licenses/")

    # Comprobar: la página es accesible y el listado está vacío.
    assert response.status_code == 200
    assert list(response.context["grants"]) == []
    assertContains(response, "Todavía no tienes licencias disponibles.")

    # Comprobar: consultar el listado no ha creado permisos.
    assert not LicenseGrant.objects.exists()


@pytest.mark.django_db
def test_license_list_shows_only_own_grants_with_fields_in_defined_order(client):
    # Preparar: dos usuarios con permisos independientes.
    owner_a = get_user_model().objects.create_user(username="license-owner-a")
    owner_b = get_user_model().objects.create_user(username="license-owner-b")

    # Preparar: fechas controladas para comprobar orden y desempate.
    recent_date = timezone.now().replace(microsecond=0)
    older_date = recent_date - timedelta(days=1)

    scenarios = [
        ("A-1", owner_a, recent_date),
        ("B-1", owner_b, recent_date),
        ("A-2", owner_a, older_date),
        ("A-3", owner_a, recent_date),
    ]
    grants = {}

    # Preparar: pedidos ya pagados, líneas históricas y permisos emitidos.
    for reference, owner, issued_at in scenarios:
        order = Order.objects.create(
            owner=owner,
            status=Order.Status.PAID,
            total_amount=Decimal("12.90"),
            currency="EUR",
        )
        item = OrderItem.objects.create(
            order=order,
            product_name=f"Producto {reference}",
            product_sku=f"SKU-{reference}",
            license_name=f"Licencia {reference}",
            terms_version="1.0",
            price=Decimal("12.90"),
            currency="EUR",
        )
        grant = LicenseGrant.objects.create(order_item=item)

        # auto_now_add asigna la fecha al crear: ajustarla para este escenario.
        LicenseGrant.objects.filter(pk=grant.pk).update(issued_at=issued_at)
        grant.refresh_from_db(from_queryset=None)
        grants[reference] = grant

    # Preparar: quien consulta es el cliente A.
    client.force_login(owner_a)

    # Actuar: abrir «Mis licencias».
    response = client.get(reverse("license_list"))

    # Comprobar: página accesible.
    assert response.status_code == 200

    # Comprobar: solo permisos de A, por fecha e identificador descendentes.
    expected_grants = [
        grants["A-3"],
        grants["A-1"],
        grants["A-2"],
    ]
    visible_grants = list(response.context["grants"])

    assert [grant.pk for grant in visible_grants] == [
        grant.pk for grant in expected_grants
    ]

    # Comprobar: aparecen los atributos de cada permiso propio.
    for grant in expected_grants:
        item = grant.order_item
        displayed_date = format_date(
            timezone.localtime(grant.issued_at),
            "DATETIME_FORMAT",
        )

        assertContains(response, f"Identificador: {grant.pk}</p>")
        assertContains(response, f"Pedido: {item.order.pk}</p>")
        assertContains(response, item.product_name)
        assertContains(response, f"SKU: {item.product_sku}")
        assertContains(response, f"Licencia: {item.license_name}")
        assertContains(response, f"Términos: {item.terms_version}")
        assertContains(response, f"Fecha de emisión: {displayed_date}")
        assertContains(response, f"Estado: {grant.get_status_display()}")

    # Comprobar: el HTML también conserva el orden esperado.
    html = response.content.decode(response.charset)
    positions = [html.index(grant.order_item.product_name) for grant in expected_grants]
    assert positions == sorted(positions)

    # Comprobar: los datos exclusivos del cliente B no aparecen.
    foreign_grant = grants["B-1"]

    assertNotContains(response, foreign_grant.order_item.product_name)
    assertNotContains(response, foreign_grant.order_item.product_sku)
    assertNotContains(response, foreign_grant.order_item.license_name)
    assertNotContains(response, f"Identificador: {foreign_grant.pk}</p>")
    assertNotContains(response, f"Pedido: {foreign_grant.order_item.order.pk}</p>")


@pytest.mark.django_db
def test_license_detail_preserves_captured_conditions_after_catalog_changes(
    client, documented_purchase
):
    # Preparar: cliente con una compra documentada y pagada.
    owner, offer, grant, expected = documented_purchase
    client.force_login(owner)

    # Preparar: guardar la línea histórica antes de cambiar el catálogo.
    item_before = OrderItem.objects.filter(pk=grant.order_item.pk).values().get()

    # Preparar: modificar el catálogo después de la compra.
    offer.product.name = "Producto modificado posteriormente"
    offer.product.sku = "SKU-POSTERIOR"
    offer.product.save(update_fields=["name", "sku"])

    license_type = offer.license_type
    license_type.name = "Licencia posterior"
    license_type.terms_version = "2.0"
    license_type.terms_text = "Condiciones nuevas exclusivas del catálogo."
    license_type.usage_scope = "Alcance posterior exclusivo del catálogo"
    license_type.save(
        update_fields=[
            "name",
            "terms_version",
            "terms_text",
            "usage_scope",
        ]
    )

    offer.grantor_name = "Concedente posterior"
    offer.rights_holder_name = "Titular posterior"
    offer.price = Decimal("99.00")
    offer.save(update_fields=["grantor_name", "rights_holder_name", "price"])

    # Actuar: consultar el detalle del permiso propio.
    response = client.get(f"/licenses/{grant.pk}/")

    # Comprobar: página accesible con todos los valores originales.
    assert response.status_code == 200

    for original_value in expected.values():
        assertContains(response, original_value)

    assertContains(response, "12,90 EUR")
    assertContains(response, f"Identificador: {grant.pk}</p>")
    assertContains(response, f"Estado: {grant.get_status_display()}")

    displayed_date = format_date(
        timezone.localtime(grant.issued_at),
        "DATETIME_FORMAT",
    )
    assertContains(response, f"Fecha de emisión: {displayed_date}")

    # Comprobar: existe un enlace al pedido del que procede el permiso.
    order_url = reverse(
        "orders:detail",
        kwargs={"order_id": grant.order_item.order.pk},
    )
    assertContains(
        response,
        f'<a href="{order_url}">Ver pedido</a>',
        html=True,
    )

    # Comprobar: no sustituye los datos históricos por los actuales.
    for current_value in [
        offer.product.name,
        offer.product.sku,
        license_type.name,
        license_type.terms_text,
        license_type.usage_scope,
        offer.grantor_name,
        offer.rights_holder_name,
    ]:
        assertNotContains(response, current_value)

    assertNotContains(response, "Términos: 2.0")
    assertNotContains(response, "99,00 EUR")
    assertNotContains(
        response,
        "Condiciones históricas pendientes de documentación",
    )

    # Comprobar: ni el cambio de catálogo ni la consulta alteran la línea.
    item_after = OrderItem.objects.filter(pk=grant.order_item.pk).values().get()
    assert item_after == item_before


@pytest.mark.django_db
def test_license_detail_does_not_expose_master_paths(
    client, monkeypatch, documented_purchase
):
    # Preparar: cliente con un permiso propio.
    owner, offer, grant, expected = documented_purchase
    client.force_login(owner)

    # Preparar: maestro privado con un nombre fácilmente identificable.
    master_filename = "rf10_secret_master_82c7.wav"
    master_name = f"masters/{master_filename}"

    product = offer.product

    Product.objects.filter(pk=product.pk).update(
        master_file=master_name,
    )
    product.refresh_from_db(from_queryset=None)

    master_path = product.master_file.path

    # Preparar: detectar cualquier intento de generar una URL del maestro.
    def fail_if_master_url_is_requested(*args, **kwargs):
        raise AssertionError("El detalle intentó generar una URL del maestro")

    monkeypatch.setattr(
        product.master_file.storage,
        "url",
        fail_if_master_url_is_requested,
    )

    # Actuar: abrir el detalle del permiso.
    response = client.get(f"/licenses/{grant.pk}/")

    # Comprobar: se muestra el detalle, no una página vacía o de error.
    assert response.status_code == 200
    assertContains(response, expected["product_name"])
    assertContains(response, expected["terms_text"])

    # Comprobar: el HTML no publica el nombre ni las rutas del maestro.
    assertNotContains(response, master_filename)
    assertNotContains(response, master_name)
    assertNotContains(response, master_path)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "missing_fields",
    [
        ("terms_text",),
        (
            "terms_text",
            "usage_scope",
            "grantor_name",
            "rights_holder_name",
        ),
    ],
    ids=["missing_historical_text", "missing_all_documentation"],
)
def test_legacy_license_detail_warns_without_using_current_conditions(
    client, documented_purchase, missing_fields
):
    # Preparar: cliente y permiso de una compra existente.
    owner, offer, grant, expected = documented_purchase
    client.force_login(owner)

    # Preparar: vaciar los campos del caso parametrizado.
    OrderItem.objects.filter(pk=grant.order_item.pk).update(
        **{field: "" for field in missing_fields},
    )

    # Preparar: el catálogo sí dispone de condiciones actuales diferentes.
    license_type = offer.license_type
    license_type.terms_version = "2.0"
    license_type.terms_text = "Texto actual que no consta en la compra antigua."
    license_type.usage_scope = "Alcance actual no documentado en la compra"
    license_type.save(update_fields=["terms_version", "terms_text", "usage_scope"])

    offer.grantor_name = "Concedente actual del catálogo"
    offer.rights_holder_name = "Titular actual del catálogo"
    offer.save(update_fields=["grantor_name", "rights_holder_name"])

    item_before = OrderItem.objects.filter(pk=grant.order_item.pk).values().get()

    # Actuar: consultar el permiso antiguo.
    response = client.get(f"/licenses/{grant.pk}/")

    # Comprobar: sigue siendo consultable y avisa de la documentación pendiente.
    assert response.status_code == 200
    assertContains(
        response,
        "Condiciones históricas pendientes de documentación",
    )

    # Comprobar: mantiene los datos históricos que sí se conocen.
    assertContains(response, expected["product_name"])
    assertContains(response, expected["product_sku"])
    assertContains(response, expected["license_name"])
    assertContains(response, f"Términos: {expected['terms_version']}")

    # Comprobar: no presenta las condiciones actuales como las compradas.
    for current_value in [
        license_type.terms_text,
        license_type.usage_scope,
        offer.grantor_name,
        offer.rights_holder_name,
    ]:
        assertNotContains(response, current_value)

    assertNotContains(response, "Términos: 2.0")

    # Comprobar: consultar tampoco rellena ni modifica la línea antigua.
    item_after = OrderItem.objects.filter(pk=grant.order_item.pk).values().get()
    assert item_after == item_before


@pytest.mark.django_db
@pytest.mark.parametrize("page", ["list", "detail"])
def test_license_access_redirects_anonymous_users_to_login(
    client, documented_purchase, page
):
    # Preparar: existe un permiso, pero el visitante no inicia sesión.
    _, _, grant, _ = documented_purchase

    if page == "list":
        url = reverse("license_list")
    else:
        url = reverse(
            "license_detail",
            kwargs={"license_id": grant.pk},
        )

    # Actuar: consultar y seguir la redirección.
    response = client.get(url, follow=True)

    # Comprobar: redirección al login con retorno a la página solicitada.
    expected_login_url = f"{reverse('users:login')}?next={url}"

    assert response.redirect_chain == [(expected_login_url, 302)]

    # Comprobar: el login es accesible y conserva el destino.
    assert response.status_code == 200
    assert response.context["next"] == url
    assert not response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_license_access_hides_foreign_and_missing_grants(
    client, settings, documented_purchase
):
    # Preparar: comprobar la respuesta de error sin información de depuración.
    settings.DEBUG = False

    owner, _, grant, expected = documented_purchase

    foreign_url = reverse(
        "license_detail",
        kwargs={"license_id": grant.pk},
    )

    # Preparar: confirmar que el permiso existe y su propietario puede verlo.
    client.force_login(owner)
    owner_response = client.get(foreign_url)

    assert owner_response.status_code == 200
    assertContains(owner_response, expected["terms_text"])

    # Preparar: iniciar sesión como otro cliente.
    other_user = get_user_model().objects.create_user(
        username="other-license-viewer",
    )
    client.force_login(other_user)

    highest_id = (
        LicenseGrant.objects.order_by("-pk").values_list("pk", flat=True).first()
    )
    assert highest_id is not None

    missing_id = highest_id + 1
    assert not LicenseGrant.objects.filter(pk=missing_id).exists()

    missing_url = reverse(
        "license_detail",
        kwargs={"license_id": missing_id},
    )

    # Actuar: consultar un identificador ajeno y otro inexistente.
    foreign_response = client.get(foreign_url)
    missing_response = client.get(missing_url)

    # Comprobar: ambas consultas reciben el mismo error.
    assert foreign_response.status_code == 404
    assert missing_response.status_code == 404
    assert foreign_response.content == missing_response.content

    # Comprobar: el error no revela datos de la compra ajena.
    for response in (foreign_response, missing_response):
        for private_value in (
            expected["product_name"],
            expected["product_sku"],
            expected["terms_text"],
            expected["grantor_name"],
            expected["rights_holder_name"],
        ):
            assertNotContains(
                response,
                private_value,
                status_code=404,
            )


@pytest.mark.django_db
@pytest.mark.parametrize("page", ["list", "detail"])
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_license_queries_reject_writes_without_changing_grants(
    documented_purchase, page, method
):
    # Preparar: propietario con un permiso existente.
    owner, _, grant, _ = documented_purchase

    # Preparar: cliente con comprobación real de CSRF.
    client = Client(enforce_csrf_checks=True)

    # Obtener la cookie CSRF desde el formulario antes de iniciar sesión.
    login_response = client.get(reverse("users:login"))
    assert login_response.status_code == 200

    client.force_login(owner)
    csrf_token = client.cookies["csrftoken"].value

    if page == "list":
        url = reverse("license_list")
    else:
        url = reverse(
            "license_detail",
            kwargs={"license_id": grant.pk},
        )

    # Preparar: conservar todos los valores de los permisos existentes.
    grants_before = list(LicenseGrant.objects.order_by("pk").values())

    # Actuar: intentar una escritura sobre una ruta de consulta.
    response = cast(
        HttpResponse,
        client.generic(
            method,
            url,
            data="{}",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        ),
    )

    # Comprobar: el método no está permitido.
    assert response.status_code == 405

    # Comprobar: no se crean, eliminan ni modifican permisos.
    grants_after = list(LicenseGrant.objects.order_by("pk").values())
    assert grants_after == grants_before


@pytest.mark.django_db
def test_authenticated_user_can_navigate_to_own_license_detail(
    client, documented_purchase
):
    # Preparar: cliente autenticado con una compra pagada y un permiso.
    owner, _, grant, expected = documented_purchase
    client.force_login(owner)

    home_url = reverse("core:home")
    list_url = reverse("license_list")
    detail_url = reverse(
        "license_detail",
        kwargs={"license_id": grant.pk},
    )

    # Actuar: abrir la página principal.
    home_response = client.get(home_url)

    # Comprobar: encuentra un enlace a «Mis licencias».
    assert home_response.status_code == 200
    assertContains(
        home_response,
        f'<a href="{list_url}">Mis licencias</a>',
        html=True,
    )

    # Actuar: consultar el destino del enlace.
    list_response = client.get(list_url)

    # Comprobar: aparece su permiso con un enlace a su detalle.
    assert list_response.status_code == 200
    assertContains(list_response, expected["product_name"])
    assertContains(
        list_response,
        f'<a href="{detail_url}">Ver condiciones de uso</a>',
        html=True,
    )

    # Actuar: consultar el destino del enlace al detalle.
    detail_response = client.get(detail_url)

    # Comprobar: se abre el permiso correcto con sus condiciones históricas.
    assert detail_response.status_code == 200
    assert detail_response.context["grant"].pk == grant.pk
    assertContains(detail_response, expected["product_name"])
    assertContains(detail_response, expected["terms_text"])


@pytest.mark.django_db
def test_license_list_query_count_does_not_grow_with_grants(
    client, documented_purchase
):
    # Preparar: usuario autenticado con un permiso y una compra pagada.
    owner, _, first_grant, expected = documented_purchase
    client.force_login(owner)

    list_url = reverse("license_list")
    expected_grant_ids = {first_grant.pk}
    expected_product_names = [expected["product_name"]]

    # Actuar: consultar el listado con un permiso y contar sus consultas.
    with CaptureQueriesContext(connection) as queries_with_one:
        first_response = client.get(list_url)

    # Comprobar: realmente se muestra el único permiso preparado.
    assert first_response.status_code == 200
    assert [grant.pk for grant in first_response.context["grants"]] == [first_grant.pk]
    assertContains(first_response, expected["product_name"])

    # Preparar: añadir cuatro permisos, cada uno con su pedido y su línea.
    # Estas escrituras quedan fuera de los bloques de medición.
    for number in range(2, 6):
        order = Order.objects.create(
            owner=owner,
            status=Order.Status.PAID,
            total_amount=Decimal("12.90"),
            currency="EUR",
        )

        product_name = f"Sonido adicional número {number}"

        item = OrderItem.objects.create(
            order=order,
            product_name=product_name,
            product_sku=f"QUERY-{number:03d}",
            license_name=expected["license_name"],
            terms_version=expected["terms_version"],
            terms_text=expected["terms_text"],
            usage_scope=expected["usage_scope"],
            grantor_name=expected["grantor_name"],
            rights_holder_name=expected["rights_holder_name"],
            price=Decimal("12.90"),
            currency="EUR",
        )

        grant = LicenseGrant.objects.create(
            order_item=item,
            status=LicenseGrant.Status.ACTIVE,
        )

        expected_grant_ids.add(grant.pk)
        expected_product_names.append(product_name)

    # Actuar: consultar el listado con cinco permisos y contar sus consultas.
    with CaptureQueriesContext(connection) as queries_with_five:
        second_response = client.get(list_url)

    # Comprobar: el listado contiene exactamente los cinco permisos.
    assert second_response.status_code == 200

    visible_grants = list(second_response.context["grants"])
    assert len(visible_grants) == 5
    assert {grant.pk for grant in visible_grants} == expected_grant_ids

    # Comprobar: los cinco productos también aparecen en el HTML.
    for product_name in expected_product_names:
        assertContains(second_response, product_name)

    # Comprobar: mostrar más permisos no aumenta las consultas SQL.
    assert len(queries_with_five) == len(queries_with_one), (
        f"Con un permiso: {len(queries_with_one)} consultas; "
        f"con cinco permisos: {len(queries_with_five)} consultas."
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view_name",
    ["license_list", "license_detail"],
    ids=["list", "detail"],
)
def test_license_read_does_not_change_business_data(
    client, documented_purchase, view_name
):
    # Preparar: usuario con pedido pagado, intento aprobado y permiso.
    owner, purchased_offer, grant, expected = documented_purchase
    client.force_login(owner)

    # Preparar: otra oferta para que el carrito tenga contenido que conservar.
    other_license_type = LicenseType.objects.create(
        name="Licencia adicional",
        slug="licencia-adicional",
        usage_scope="Uso adicional de prueba",
        summary="Otra opción de compra",
        terms_version="1.0",
        terms_text="Condiciones de la oferta adicional.",
    )

    cart_offer = ProductLicenseOffer.objects.create(
        product=purchased_offer.product,
        license_type=other_license_type,
        price=Decimal("5.90"),
        currency="EUR",
        grantor_name="Distribuidora de prueba",
        rights_holder_name="Estudio titular de prueba",
    )
    add_offer_to_cart(owner=owner, offer_id=cart_offer.pk)

    assert CartItem.objects.filter(
        cart__owner=owner,
        offer=cart_offer,
    ).exists()

    # Preparar: guardar los registros y sus valores antes de consultar.
    before = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
        "grants": list(LicenseGrant.objects.order_by("pk").values()),
    }

    # Preparar: seleccionar la URL del caso parametrizado.
    if view_name == "license_detail":
        url = reverse(
            view_name,
            kwargs={"license_id": grant.pk},
        )
    else:
        url = reverse(view_name)

    # Actuar: consultar el listado o el detalle.
    response = client.get(url)

    # Comprobar: la consulta funciona y muestra el producto comprado.
    assert response.status_code == 200
    assertContains(response, expected["product_name"])

    # Comprobar: volver a leer el estado persistido.
    after = {
        "orders": list(Order.objects.order_by("pk").values()),
        "order_items": list(OrderItem.objects.order_by("pk").values()),
        "attempts": list(PaymentAttempt.objects.order_by("pk").values()),
        "carts": list(Cart.objects.order_by("pk").values()),
        "cart_items": list(CartItem.objects.order_by("pk").values()),
        "grants": list(LicenseGrant.objects.order_by("pk").values()),
    }

    # Comprobar: no se ha creado, eliminado ni modificado ningún registro.
    assert after == before


@pytest.mark.django_db
def test_cart_conversion_preserves_product_reference_after_sku_changes(client):
    # Preparar: usuario autenticado y oferta con condiciones completas.
    owner = get_user_model().objects.create_user(
        username="stable-product-owner",
    )
    client.force_login(owner)

    offer = create_available_offer(
        terms_text="Condiciones originales de la compra.",
    )

    offer.grantor_name = "Concedente original"
    offer.rights_holder_name = "Titular original"
    offer.save(update_fields=["grantor_name", "rights_holder_name"])

    # Preparar: conservar la referencia técnica y los valores esperados.
    product_id_before = offer.product.pk

    expected_snapshots = {
        "product_sku": offer.product.sku,
        "product_name": offer.product.name,
        "license_name": offer.license_type.name,
        "terms_version": offer.license_type.terms_version,
        "terms_text": offer.license_type.terms_text,
        "usage_scope": offer.license_type.usage_scope,
        "grantor_name": offer.grantor_name,
        "rights_holder_name": offer.rights_holder_name,
        "price": offer.price,
        "currency": offer.currency,
    }

    add_offer_to_cart(owner=owner, offer_id=offer.pk)

    # Actuar: convertir el carrito en un pedido mediante la vista.
    response = client.post(reverse("orders:create"))

    # Comprobar: se crea el pedido con una línea vinculada al producto original.
    assert response.status_code == 302

    order = Order.objects.get(owner=owner)
    item = OrderItem.objects.get(order=order)

    assert item.source_product is not None
    assert item.source_product.pk == product_id_before

    assert item.source_license_type is not None
    assert item.source_license_type.pk == offer.license_type.pk

    captured_snapshots = (
        OrderItem.objects.filter(pk=item.pk).values(*expected_snapshots.keys()).get()
    )
    assert captured_snapshots == expected_snapshots

    # Conservar toda la línea antes del cambio de catálogo.
    item_before = OrderItem.objects.filter(pk=item.pk).values().get()

    # Actuar: modificar el SKU y el nombre del producto en el catálogo.
    product = offer.product
    product.sku = "SKU-MODIFICADO"
    product.name = "Nombre posterior a la compra"
    product.save(update_fields=["sku", "name"])

    # Comprobar: la referencia continúa apuntando al mismo producto.
    item.refresh_from_db(from_queryset=None)

    assert item.source_product is not None
    product_id_after = item.source_product.pk

    assert product_id_after == product_id_before
    assert item.source_product.sku == "SKU-MODIFICADO"

    # Comprobar: los valores guardados en la línea no han cambiado.
    item_after = OrderItem.objects.filter(pk=item.pk).values().get()
    assert item_after == item_before

    # Actuar: aprobar el pago del pedido que contiene los datos capturados.
    payment_response = client.post(
        reverse(
            "orders:simulate_payment",
            kwargs={"order_id": order.pk},
        ),
        {
            "result": PaymentAttempt.Result.APPROVED,
            "idempotency_key": str(uuid4()),
        },
    )

    assert payment_response.status_code == 302

    # Comprobar: el pago no modifica la línea histórica.
    item_after_payment = OrderItem.objects.filter(pk=item.pk).values().get()
    assert item_after_payment == item_before

    # Comprobar: el permiso corresponde a esa misma línea.
    grant = LicenseGrant.objects.get(order_item=item)
    assert grant.status == LicenseGrant.Status.ACTIVE

    # Actuar: consultar las condiciones del permiso emitido.
    detail_response = client.get(
        reverse(
            "license_detail",
            kwargs={"license_id": grant.pk},
        ),
    )

    # Comprobar: muestra los datos originales capturados desde el servidor.
    assert detail_response.status_code == 200
    assert detail_response.context["item"].pk == item.pk

    for field in (
        "product_name",
        "product_sku",
        "license_name",
        "terms_version",
        "terms_text",
        "usage_scope",
        "grantor_name",
        "rights_holder_name",
    ):
        assertContains(detail_response, expected_snapshots[field])

    # Comprobar: consultar tampoco modifica la captura.
    assert OrderItem.objects.filter(pk=item.pk).values().get() == item_before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view_name",
    ["orders:detail", "license_detail"],
    ids=["order_detail", "license_detail"],
)
def test_unmapped_order_item_remains_readable_and_pending_delivery(client, view_name):
    # Preparar: usuario autenticado.
    owner = get_user_model().objects.create_user(
        username="unmapped-order-owner",
    )
    client.force_login(owner)

    # Preparar: un producto actual con el mismo SKU que la línea antigua.
    # Esa coincidencia no debe provocar una asociación automática.
    offer = create_available_offer()

    # Preparar: compra antigua pagada, sin referencia técnica al producto.
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PAID,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    item = OrderItem.objects.create(
        order=order,
        product_name="Nombre histórico del producto",
        product_sku=offer.product.sku,
        license_name="Licencia histórica",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )

    grant = LicenseGrant.objects.create(
        order_item=item,
        status=LicenseGrant.Status.ACTIVE,
    )

    assert item.source_product is None

    item_before = OrderItem.objects.filter(pk=item.pk).values().get()

    # Preparar: seleccionar la página de esta ejecución.
    if view_name == "orders:detail":
        url = reverse(view_name, kwargs={"order_id": order.pk})
    else:
        url = reverse(view_name, kwargs={"license_id": grant.pk})

    # Actuar: consultar la compra antigua.
    response = client.get(url)

    # Comprobar: permanece accesible con sus datos históricos.
    assert response.status_code == 200
    assertContains(response, item.product_name)
    assertContains(response, item.product_sku)
    assertContains(response, item.license_name)
    assertContains(response, "Términos: 1.0")
    assertContains(response, "12,90 EUR")

    # Comprobar: se identifica como pendiente de preparación de entrega.
    assertContains(response, "Pendiente de preparación de entrega")

    # Comprobar: consultar no reconstruye la referencia ni modifica la línea.
    item.refresh_from_db(from_queryset=None)
    assert item.source_product is None

    item_after = OrderItem.objects.filter(pk=item.pk).values().get()
    assert item_after == item_before


@pytest.mark.django_db
@pytest.mark.parametrize("stage", ["cart", "checkout", "payment"])
@pytest.mark.parametrize(
    "catalog_change",
    [
        "none",
        "price",
        "currency",
        "product_name",
        "license_name",
        "sku",
        "terms_version",
    ],
)
def test_rf10_repurchase_is_rejected_without_business_changes(
    client, prepared_purchase_offer, stage, catalog_change
):
    # Preparar: primera compra pendiente.
    owner, offer = prepared_purchase_offer
    client.force_login(owner)

    original_order = prepare_pending_order(owner, offer)

    # Preparar el segundo recorrido antes de adquirir el primer permiso.
    if stage == "checkout":
        add_offer_to_cart(owner=owner, offer_id=offer.pk)
    elif stage == "payment":
        second_order = prepare_pending_order(owner, offer)

    # Preparar: aprobar la primera compra.
    approved_response = request_payment_approval(client, original_order)
    assert approved_response.status_code == 302

    original_grant = LicenseGrant.objects.get(
        order_item__order=original_order,
    )
    assert original_grant.status == LicenseGrant.Status.ACTIVE

    # Preparar: cambiar un dato que no debe alterar la identidad adquirida.
    if catalog_change == "price":
        offer.price = Decimal("29.90")
        offer.save(update_fields=["price"])
    elif catalog_change == "currency":
        offer.currency = "USD"
        offer.save(update_fields=["currency"])
    elif catalog_change == "product_name":
        offer.product.name = "Producto renombrado"
        offer.product.save(update_fields=["name"])
    elif catalog_change == "license_name":
        offer.license_type.name = "Tipo de licencia renombrado"
        offer.license_type.save(update_fields=["name"])
    elif catalog_change == "sku":
        offer.product.sku = "SKU-RENOMBRADO"
        offer.product.save(update_fields=["sku"])
    elif catalog_change == "terms_version":
        offer.license_type.terms_version = "2.0"
        offer.license_type.terms_text = "Condiciones posteriores."
        offer.license_type.save(
            update_fields=["terms_version", "terms_text"],
        )

    before = capture_purchase_business_data()

    # Actuar: intentar adquirir de nuevo la misma combinación.
    if stage == "cart":
        response = client.post(
            reverse("cart:add-item"),
            {"offer_id": offer.pk},
        )
    elif stage == "checkout":
        response = client.post(reverse("orders:create"))
    else:
        response = request_payment_approval(client, second_order)

    # Comprobar: rechazo comprensible.
    assertContains(
        response,
        "Ya tienes un permiso activo para este producto y tipo de licencia.",
        status_code=409,
    )

    # Comprobar: no cambia ningún dato de negocio.
    after = capture_purchase_business_data()
    assert after == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "scenario",
    ["other_customer", "other_product", "other_license_type"],
)
def test_rf10_repurchase_rule_allows_distinct_acquisitions(
    client, prepared_purchase_offer, scenario
):
    # Preparar: una combinación ya adquirida por el primer cliente.
    owner, offer = prepared_purchase_offer
    original_order = prepare_pending_order(owner, offer)

    client.force_login(owner)
    assert request_payment_approval(client, original_order).status_code == 302

    buyer = owner
    candidate_offer = offer

    # Preparar: cambiar únicamente el elemento que permite otra adquisición.
    if scenario == "other_customer":
        buyer = get_user_model().objects.create_user(
            username="rf10-other-customer",
        )

    elif scenario == "other_product":
        other_product = Product.objects.create(
            category=offer.product.category,
            name="Otro producto",
            slug="rf10-other-product",
            sku="RF10-OTHER",
            summary="Otro sonido",
            description="Producto diferente para la prueba.",
            duration_ms=1000,
            audio_format="wav",
            sample_rate_hz=48000,
            bit_depth=24,
        )
        candidate_offer = ProductLicenseOffer.objects.create(
            product=other_product,
            license_type=offer.license_type,
            price=Decimal("8.00"),
            currency="EUR",
            grantor_name=offer.grantor_name,
            rights_holder_name=offer.rights_holder_name,
        )

    else:
        other_license_type = LicenseType.objects.create(
            name="Otro tipo de licencia",
            slug="rf10-other-license",
            usage_scope="Otro alcance",
            summary="Otra licencia",
            terms_version="1.0",
            terms_text="Condiciones completas de la otra licencia.",
        )
        candidate_offer = ProductLicenseOffer.objects.create(
            product=offer.product,
            license_type=other_license_type,
            price=Decimal("8.00"),
            currency="EUR",
            grantor_name=offer.grantor_name,
            rights_holder_name=offer.rights_holder_name,
        )

    client.force_login(buyer)

    # Actuar y comprobar: puede añadir la oferta.
    add_response = client.post(
        reverse("cart:add-item"),
        {"offer_id": candidate_offer.pk},
    )
    assert add_response.status_code == 302
    assert CartItem.objects.filter(
        cart__owner=buyer,
        offer=candidate_offer,
    ).exists()

    # Actuar y comprobar: puede convertir el carrito.
    checkout_response = client.post(reverse("orders:create"))
    assert checkout_response.status_code == 302

    new_order = Order.objects.get(
        owner=buyer,
        status=Order.Status.PENDING_PAYMENT,
    )

    # Actuar y comprobar: puede pagar y obtener su permiso.
    payment_response = request_payment_approval(client, new_order)
    assert payment_response.status_code == 302

    new_order.refresh_from_db(from_queryset=None)
    assert new_order.status == Order.Status.PAID

    grant = LicenseGrant.objects.get(order_item__order=new_order)
    assert grant.status == LicenseGrant.Status.ACTIVE
    assert grant.order_item.order.owner.pk == buyer.pk

    assert LicenseGrant.objects.count() == 2


@pytest.mark.django_db
def test_rf10_original_payment_replay_preserves_success(
    client, prepared_purchase_offer
):
    # Preparar: compra aprobada con una clave conocida.
    owner, offer = prepared_purchase_offer
    client.force_login(owner)

    order = prepare_pending_order(owner, offer)
    payment_key = uuid4()

    first_response = request_payment_approval(client, order, payment_key)
    assert first_response.status_code == 302
    assert LicenseGrant.objects.filter(order_item__order=order).count() == 1

    before = capture_purchase_business_data()

    # Actuar: repetir el mismo pago, aunque ya exista el permiso.
    repeated_response = request_payment_approval(client, order, payment_key)

    # Comprobar: conserva el éxito sin ejecutar otra adquisición.
    assert repeated_response.status_code == 302
    assert repeated_response["Location"] == reverse(
        "orders:detail",
        kwargs={"order_id": order.pk},
    )
    assert capture_purchase_business_data() == before


@pytest.mark.django_db(transaction=True)
def test_rf10_concurrent_orders_cannot_acquire_same_combination_twice(
    prepared_purchase_offer,
):
    # Preparar: dos pedidos pendientes del mismo cliente y combinación.
    owner, offer = prepared_purchase_offer
    first_order = prepare_pending_order(owner, offer)
    second_order = prepare_pending_order(owner, offer)

    start = Barrier(2)

    def approve_order(order):
        try:
            thread_client = Client()
            thread_client.force_login(owner)

            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend_pid = cursor.fetchone()[0]
                cursor.execute("SET lock_timeout = '5s'")
                cursor.execute("SET statement_timeout = '10s'")

            start.wait(timeout=10)
            response = request_payment_approval(thread_client, order)

            return order.pk, response.status_code, backend_pid
        finally:
            connections.close_all()

    # Actuar: intentar aprobar ambas compras concurrentemente.
    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(approve_order, first_order)
        second_future = executor.submit(approve_order, second_order)

        results = [
            first_future.result(timeout=30),
            second_future.result(timeout=30),
        ]

    # Comprobar: participaron conexiones diferentes y solo una tuvo éxito.
    assert len({backend_pid for _, _, backend_pid in results}) == 2
    assert sorted(status for _, status, _ in results) == [302, 409]

    # Comprobar: quien gana queda pagado con intento y permiso.
    # Quien pierde queda pendiente sin intento ni permiso.
    for order_id, status, _ in results:
        order = Order.objects.get(pk=order_id)

        if status == 302:
            assert order.status == Order.Status.PAID

            attempt = PaymentAttempt.objects.get(order=order)
            assert attempt.result == PaymentAttempt.Result.APPROVED

            grant = LicenseGrant.objects.get(order_item__order=order)
            assert grant.status == LicenseGrant.Status.ACTIVE
        else:
            assert order.status == Order.Status.PENDING_PAYMENT
            assert not PaymentAttempt.objects.filter(order=order).exists()
            assert not LicenseGrant.objects.filter(
                order_item__order=order,
            ).exists()

    assert PaymentAttempt.objects.count() == 1
    assert LicenseGrant.objects.count() == 1


@pytest.mark.django_db
def test_rf10_pending_order_preserves_conditions_through_payment(
    client, prepared_purchase_offer
):
    # Preparar: pedido pendiente que ya ha capturado condiciones.
    owner, offer = prepared_purchase_offer
    client.force_login(owner)

    order = prepare_pending_order(owner, offer)
    item = OrderItem.objects.get(order=order)

    item_before = OrderItem.objects.filter(pk=item.pk).values().get()

    original_conditions = {
        "terms_version": item.terms_version,
        "terms_text": item.terms_text,
        "usage_scope": item.usage_scope,
        "grantor_name": item.grantor_name,
        "rights_holder_name": item.rights_holder_name,
    }

    # Preparar: publicar condiciones diferentes después de crear el pedido.
    license_type = offer.license_type
    license_type.terms_version = "2.0"
    license_type.terms_text = "Texto posterior del catálogo."
    license_type.usage_scope = "Alcance posterior del catálogo"
    license_type.save(
        update_fields=["terms_version", "terms_text", "usage_scope"],
    )

    offer.grantor_name = "Concedente posterior"
    offer.rights_holder_name = "Titular posterior"
    offer.save(update_fields=["grantor_name", "rights_holder_name"])

    # Actuar: consultar el pedido todavía pendiente.
    pending_response = client.get(
        reverse("orders:detail", kwargs={"order_id": order.pk}),
    )

    assert pending_response.status_code == 200
    assertContains(pending_response, "Términos: 1.0")
    assert OrderItem.objects.filter(pk=item.pk).values().get() == item_before

    # Actuar: aprobar el pago después del cambio de catálogo.
    payment_response = request_payment_approval(client, order)
    assert payment_response.status_code == 302

    grant = LicenseGrant.objects.get(order_item=item)

    # Actuar: consultar las condiciones del permiso emitido.
    detail_response = client.get(
        reverse("license_detail", kwargs={"license_id": grant.pk}),
    )

    # Comprobar: el permiso muestra exactamente lo capturado al crear el pedido.
    assert detail_response.status_code == 200

    for value in original_conditions.values():
        assertContains(detail_response, value)

    assertNotContains(detail_response, license_type.terms_text)
    assertNotContains(detail_response, license_type.usage_scope)
    assertNotContains(detail_response, offer.grantor_name)
    assertNotContains(detail_response, offer.rights_holder_name)

    assert OrderItem.objects.filter(pk=item.pk).values().get() == item_before


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field", "new_value"),
    [
        ("terms_text", "Texto cambiado sin nueva versión."),
        ("usage_scope", "Alcance cambiado sin nueva versión"),
    ],
)
def test_rf10_license_content_change_requires_new_version(
    prepared_purchase_offer, field, new_value
):
    # Preparar: condiciones ya capturadas en un pedido.
    owner, offer = prepared_purchase_offer
    prepare_pending_order(owner, offer)

    license_type = offer.license_type
    catalog_before = (
        LicenseType.objects.filter(
            pk=license_type.pk,
        )
        .values()
        .get()
    )
    business_before = capture_purchase_business_data()

    setattr(license_type, field, new_value)

    # Actuar y comprobar: guardar contenido distinto con la misma versión falla.
    with pytest.raises(ValidationError):
        license_type.save(update_fields=[field])

    # Comprobar: ni el catálogo ni las compras históricas se sobrescriben.
    catalog_after = (
        LicenseType.objects.filter(
            pk=license_type.pk,
        )
        .values()
        .get()
    )

    assert catalog_after == catalog_before
    assert capture_purchase_business_data() == business_before


@pytest.mark.django_db
def test_rf10_customer_can_read_conditions_before_creating_order(
    client, prepared_purchase_offer
):
    # Preparar: cliente y oferta disponible, sin pedido.
    owner, offer = prepared_purchase_offer
    client.force_login(owner)

    assert not Order.objects.filter(owner=owner).exists()
    before = capture_purchase_business_data()

    # Actuar: abrir la página desde la que se selecciona la oferta.
    response = client.get(
        reverse(
            "catalog:product-detail",
            kwargs={"slug": offer.product.slug},
        ),
    )

    # Comprobar: texto completo y versión disponibles antes del pedido.
    assert response.status_code == 200
    assertContains(response, offer.license_type.terms_text)
    assertContains(response, offer.license_type.terms_version)

    # Comprobar: la consulta no crea ni modifica datos de compra.
    assert capture_purchase_business_data() == before


@pytest.mark.django_db
@pytest.mark.parametrize("stage", ["checkout", "payment"])
@pytest.mark.parametrize(
    "missing_field",
    [
        "terms_version",
        "terms_text",
        "usage_scope",
        "grantor_name",
        "rights_holder_name",
    ],
)
@pytest.mark.parametrize("empty_value", ["", "   "], ids=["empty", "spaces"])
def test_rf10_incomplete_conditions_reject_operation_without_changes(
    client, prepared_purchase_offer, stage, missing_field, empty_value
):
    # Preparar: usuario autenticado y oferta inicialmente completa.
    owner, offer = prepared_purchase_offer
    client.force_login(owner)

    if stage == "checkout":
        add_offer_to_cart(owner=owner, offer_id=offer.pk)

        # Simular documentación incompleta en los datos del catálogo.
        if missing_field in ("grantor_name", "rights_holder_name"):
            ProductLicenseOffer.objects.filter(pk=offer.pk).update(
                **{missing_field: empty_value},
            )
        else:
            LicenseType.objects.filter(pk=offer.license_type.pk).update(
                **{missing_field: empty_value},
            )
    else:
        order = prepare_pending_order(owner, offer)

        # Simular un pedido pendiente con documentación histórica incompleta.
        OrderItem.objects.filter(order=order).update(
            **{missing_field: empty_value},
        )

    # Guardar el estado una vez preparado el defecto.
    before = capture_purchase_business_data()

    # Actuar: intentar convertir el carrito o aprobar el pedido incompleto.
    if stage == "checkout":
        response = client.post(reverse("orders:create"))
    else:
        response = request_payment_approval(client, order)

    # Comprobar: rechazo sin efectos parciales.
    assert response.status_code == 409
    assert capture_purchase_business_data() == before


@pytest.mark.django_db
@pytest.mark.parametrize("stage", ["cart", "checkout", "payment"])
@pytest.mark.parametrize(
    "missing_reference",
    ["product", "license_type", "both"],
)
def test_unresolved_previous_purchase_blocks_possible_repurchase(
    client,
    prepared_purchase_offer,
    stage,
    missing_reference,
):
    # Preparar: cliente autenticado y oferta con condiciones completas.
    owner, offer = prepared_purchase_offer
    client.force_login(owner)

    # Preparar: dejar listo el recorrido antes de introducir la compra antigua.
    pending_order = None

    if stage == "checkout":
        add_offer_to_cart(owner=owner, offer_id=offer.pk)
    elif stage == "payment":
        pending_order = prepare_pending_order(owner, offer)

    # Preparar: compra antigua pagada con una identidad incompleta.
    legacy_order = Order.objects.create(
        owner=owner,
        status=Order.Status.PAID,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )
    legacy_item = OrderItem.objects.create(
        order=legacy_order,
        source_product=(
            None if missing_reference in ("product", "both") else offer.product
        ),
        source_license_type=(
            None
            if missing_reference in ("license_type", "both")
            else offer.license_type
        ),
        product_name="Nombre histórico del producto",
        product_sku="SKU-HISTORICO",
        license_name="Nombre histórico de la licencia",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )
    LicenseGrant.objects.create(
        order_item=legacy_item,
        status=LicenseGrant.Status.ACTIVE,
    )

    # Preparar: guardar todos los datos de negocio antes de la solicitud.
    before = capture_purchase_business_data()

    # Actuar: intentar adquirir una combinación que podría estar comprada.
    if stage == "cart":
        response = client.post(
            reverse("cart:add-item"),
            {"offer_id": offer.pk},
        )
    elif stage == "checkout":
        response = client.post(reverse("orders:create"))
    else:
        assert pending_order is not None
        response = request_payment_approval(client, pending_order)

    # Comprobar: rechazo comprensible por identidad pendiente de revisión.
    assertContains(
        response,
        "Una compra anterior necesita revisión antes de adquirir esta licencia.",
        status_code=409,
    )

    # Comprobar: no se modifica ningún dato ni se inventan referencias.
    assert capture_purchase_business_data() == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "missing_fields",
    [
        ("source_product",),
        ("source_license_type",),
        ("source_product", "source_license_type"),
    ],
    ids=["missing_product", "missing_license_type", "missing_both"],
)
def test_payment_rejects_pending_order_with_unresolved_identity(
    client,
    prepared_purchase_offer,
    missing_fields,
):
    # Preparar: cliente autenticado y pedido con condiciones completas.
    owner, offer = prepared_purchase_offer
    client.force_login(owner)
    order = prepare_pending_order(owner, offer)

    # Preparar: representar un pedido pendiente con referencias sin resolver.
    OrderItem.objects.filter(order=order).update(
        **{field: None for field in missing_fields},
    )

    # Preparar: guardar los datos antes de intentar el pago.
    before = capture_purchase_business_data()

    # Actuar: solicitar la aprobación.
    response = request_payment_approval(client, order)

    # Comprobar: rechazo comprensible por identidad incompleta.
    assertContains(
        response,
        "El pedido necesita revisión: contiene líneas sin identificar.",
        status_code=409,
    )

    # Comprobar: no hay intento, cambio de estado ni permisos nuevos.
    assert capture_purchase_business_data() == before


@pytest.mark.django_db
def test_license_detail_query_count_does_not_grow_with_owned_grants(
    client, documented_purchase
):
    # Preparar: propietario con un permiso y un detalle propio consultable.
    owner, _, first_grant, expected = documented_purchase
    client.force_login(owner)
    detail_url = reverse("license_detail", kwargs={"license_id": first_grant.pk})

    # Actuar: medir la consulta del detalle con un único permiso propio.
    with CaptureQueriesContext(connection) as queries_with_one:
        first_response = client.get(detail_url)

    assert first_response.status_code == 200
    assertContains(first_response, expected["terms_text"])

    # Preparar: añadir cuatro compras fuera del bloque de medición.
    for number in range(2, 6):
        order = Order.objects.create(
            owner=owner,
            status=Order.Status.PAID,
            total_amount=Decimal("12.90"),
            currency="EUR",
        )
        item = OrderItem.objects.create(
            order=order,
            product_name=f"Sonido adicional {number}",
            product_sku=f"DETAIL-{number}",
            license_name=expected["license_name"],
            terms_version=expected["terms_version"],
            terms_text=expected["terms_text"],
            usage_scope=expected["usage_scope"],
            grantor_name=expected["grantor_name"],
            rights_holder_name=expected["rights_holder_name"],
            price=Decimal("12.90"),
            currency="EUR",
        )
        LicenseGrant.objects.create(order_item=item)

    assert LicenseGrant.objects.filter(order_item__order__owner=owner).count() == 5

    # Actuar: medir el mismo detalle cuando el propietario ya tiene cinco permisos.
    with CaptureQueriesContext(connection) as queries_with_five:
        second_response = client.get(detail_url)

    # Comprobar: sigue mostrando el permiso solicitado con consultas constantes.
    assert second_response.status_code == 200
    assert second_response.context["grant"].pk == first_grant.pk
    assertContains(second_response, expected["terms_text"])
    assert len(queries_with_five) == len(queries_with_one)
