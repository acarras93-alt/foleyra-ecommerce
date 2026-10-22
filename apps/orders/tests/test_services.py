from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains

from apps.cart.models import CartItem
from apps.cart.services import add_offer_to_cart
from apps.catalog.models import (
    Category,
    LicenseType,
    MasterAudioPreparation,
    Product,
    ProductLicenseOffer,
    private_master_storage,
)
from apps.catalog.services import set_product_master_audio
from apps.orders import services as order_services
from apps.orders.models import LicenseGrant, Order, OrderItem, PaymentAttempt
from apps.orders.services import EmptyCart, OfferNotAvailable, create_order_from_cart
from apps.orders.tests.helpers import create_master_wav_bytes, prepare_product_master


def create_available_offer(
    *,
    terms_text="Condiciones completas de prueba.",
    usage_scope="Uso de prueba",
    with_master=True,
):
    category = Category.objects.create(
        name="Pedidos",
        slug="pedidos",
    )
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
    if with_master:
        prepare_product_master(product)

    license_type = LicenseType.objects.create(
        name="Licencia de pedido",
        slug="licencia-pedido",
        usage_scope=usage_scope,
        summary="Resumen de licencia de prueba.",
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
    preparation = prepare_product_master(product)

    return OrderItem.objects.create(
        order=order,
        source_product=product,
        source_license_type=license_type,
        master_preparation=preparation,
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
        total_amount=Decimal("31.30"),
        currency="EUR",
    )

    first_item = create_payable_order_item(
        order=order,
        product_name="Impacto cinematográfico",
        product_sku="PED-001",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )

    second_item = create_payable_order_item(
        order=order,
        product_name="Pasos sobre madera",
        product_sku="PED-002",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("8.50"),
        currency="EUR",
    )

    third_item = create_payable_order_item(
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
    assert order.total_amount == Decimal("31.30")
    assert order.currency == "EUR"

    # Crear: exactamente un intento aprobado con los datos esperados.
    attempts = PaymentAttempt.objects.filter(order=order)
    assert attempts.count() == 1

    attempt = attempts.get()
    assert attempt.result == "approved"
    assert attempt.idempotency_key == payment_key
    assert attempt.amount == Decimal("31.30")
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

    create_payable_order_item(
        order=order,
        product_name="Impacto cinematográfico",
        product_sku="PED-001",
        license_name="Licencia comercial",
        terms_version="1.0",
        price=Decimal("12.90"),
        currency="EUR",
    )

    create_payable_order_item(
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
def test_regularization_creates_only_missing_grants_for_paid_orders():
    # Preparar: propietario de las compras antiguas.
    owner = get_user_model().objects.create_user(
        username="legacy-orders-owner",
    )

    # Preparar: pedido pagado con dos líneas y pedido pendiente con una.
    paid_order = Order.objects.create(
        owner=owner,
        status=Order.Status.PAID,
        total_amount=Decimal("25.80"),
        currency="EUR",
    )
    pending_order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )

    items = []
    for order, sku in [
        (paid_order, "LEGACY-001"),
        (paid_order, "LEGACY-002"),
        (pending_order, "LEGACY-003"),
    ]:
        items.append(
            OrderItem.objects.create(
                order=order,
                product_sku=sku,
                product_name=f"Producto {sku}",
                license_name="Licencia comercial",
                terms_version="1.0",
                price=Decimal("12.90"),
                currency="EUR",
            )
        )

    existing_item, missing_item, pending_item = items

    # Preparar: un permiso ya existente que debe conservarse.
    existing_grant = LicenseGrant.objects.create(
        order_item=existing_item,
        status=LicenseGrant.Status.ACTIVE,
    )

    # Preparar: intento aprobado histórico que no debe modificarse.
    PaymentAttempt.objects.create(
        order=paid_order,
        idempotency_key=uuid4(),
        result=PaymentAttempt.Result.APPROVED,
        amount=paid_order.total_amount,
        currency=paid_order.currency,
    )

    # Preparar: guardar pedidos, intentos y líneas, incluida su falta de texto.
    business_before = {
        model.__name__: list(model.objects.order_by("pk").values())
        for model in (Order, OrderItem, PaymentAttempt)
    }
    existing_grant_before = (
        LicenseGrant.objects.filter(pk=existing_grant.pk).values().get()
    )

    assert missing_item.terms_text == ""
    selected_order_ids = [paid_order.pk, pending_order.pk]

    # Actuar: regularizar explícitamente los pedidos seleccionados.
    created_count = order_services.regularize_paid_order_grants(
        order_ids=selected_order_ids,
    )

    # Comprobar: se crea únicamente el permiso faltante del pedido pagado.
    assert created_count == 1
    assert LicenseGrant.objects.count() == 2

    new_grant = LicenseGrant.objects.get(order_item=missing_item)
    assert new_grant.status == LicenseGrant.Status.ACTIVE
    assert new_grant.issued_at is not None
    assert not LicenseGrant.objects.filter(order_item=pending_item).exists()

    # Comprobar: el permiso existente conserva todos sus valores.
    assert (
        LicenseGrant.objects.filter(pk=existing_grant.pk).values().get()
        == existing_grant_before
    )

    # Comprobar: no se alteran pedidos, intentos ni condiciones históricas.
    business_after = {
        model.__name__: list(model.objects.order_by("pk").values())
        for model in (Order, OrderItem, PaymentAttempt)
    }
    assert business_after == business_before

    # Preparar: conservar los permisos tras la primera regularización.
    grants_before_replay = list(LicenseGrant.objects.order_by("pk").values())

    # Actuar: repetir la misma operación.
    replay_count = order_services.regularize_paid_order_grants(
        order_ids=selected_order_ids,
    )

    # Comprobar: no crea permisos ni modifica los existentes.
    assert replay_count == 0
    assert list(LicenseGrant.objects.order_by("pk").values()) == grants_before_replay

    # Comprobar: la repetición tampoco altera los datos históricos.
    business_after_replay = {
        model.__name__: list(model.objects.order_by("pk").values())
        for model in (Order, OrderItem, PaymentAttempt)
    }
    assert business_after_replay == business_before


@pytest.mark.django_db
def test_legacy_documentation_fills_missing_data_and_preserves_snapshots():
    # Preparar: cliente y administrador que revisó la documentación.
    owner = get_user_model().objects.create_user(
        username="legacy-documentation-owner",
    )
    reviewer = get_user_model().objects.create_user(
        username="legacy-documentation-reviewer",
        is_staff=True,
    )

    # Preparar: el catálogo actual ya contiene otras condiciones.
    offer = create_available_offer(
        terms_text="Condiciones actuales de la versión 2.0.",
        usage_scope="Alcance actual del catálogo",
    )
    offer.license_type.terms_version = "2.0"
    offer.license_type.save(update_fields=["terms_version"])

    offer.grantor_name = "Concedente actual"
    offer.rights_holder_name = "Titular actual"
    offer.save(update_fields=["grantor_name", "rights_holder_name"])

    # Preparar: compra antigua con algunos datos históricos conocidos.
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PAID,
        total_amount=Decimal("8.50"),
        currency="EUR",
    )
    item = OrderItem.objects.create(
        order=order,
        product_sku="SKU-HISTORICO",
        product_name="Nombre histórico del sonido",
        license_name="Licencia histórica",
        terms_version="1.0",
        usage_scope="Proyectos audiovisuales",
        price=Decimal("8.50"),
        currency="EUR",
    )
    LicenseGrant.objects.create(order_item=item)

    # Preparar: correspondencia explícita respaldada por un documento revisado.
    mapping = {
        "order_item_id": item.pk,
        "source_product_id": offer.product.pk,
        "source_license_type_id": offer.license_type.pk,
        "terms_version": "1.0",
        "terms_text": "Texto histórico completo de la versión 1.0.",
        "usage_scope": "Proyectos audiovisuales",
        "grantor_name": "Concedente histórico",
        "rights_holder_name": "Titular histórico",
        "evidence_reference": "archivo-historico/condiciones-v1-documento-001",
        "reviewed_by_id": reviewer.pk,
        "reviewed_at": timezone.now(),
    }

    # Preparar: conservar la línea y los registros ajenos a la documentación.
    item_before = OrderItem.objects.filter(pk=item.pk).values().get()
    unchanged_models = (
        Order,
        PaymentAttempt,
        LicenseGrant,
        Product,
        LicenseType,
        ProductLicenseOffer,
    )
    business_before = {
        model.__name__: list(model.objects.order_by("pk").values())
        for model in unchanged_models
    }

    # Actuar: aplicar la correspondencia histórica revisada.
    order_services.regularize_legacy_order_item(
        order_item_id=item.pk,
        mappings=[mapping],
    )

    # Comprobar: únicamente se completan los campos que estaban ausentes.
    expected_item = {
        **item_before,
        "source_product_id": offer.product.pk,
        "source_license_type_id": offer.license_type.pk,
        "terms_text": mapping["terms_text"],
        "grantor_name": mapping["grantor_name"],
        "rights_holder_name": mapping["rights_holder_name"],
    }
    item_after = OrderItem.objects.filter(pk=item.pk).values().get()

    assert item_after == expected_item

    # Comprobar: se conserva la versión comprada y no se usa el texto actual.
    assert item_after["terms_version"] == "1.0"
    assert item_after["terms_text"] != offer.license_type.terms_text

    # Comprobar: no se alteran pedidos, pagos, permisos ni catálogo.
    business_after = {
        model.__name__: list(model.objects.order_by("pk").values())
        for model in unchanged_models
    }
    assert business_after == business_before

    # Actuar: repetir exactamente la misma regularización.
    order_services.regularize_legacy_order_item(
        order_item_id=item.pk,
        mappings=[mapping],
    )

    # Comprobar: la repetición no modifica la línea ni los demás registros.
    assert OrderItem.objects.filter(pk=item.pk).values().get() == item_after

    business_after_replay = {
        model.__name__: list(model.objects.order_by("pk").values())
        for model in unchanged_models
    }
    assert business_after_replay == business_before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "scenario",
    [
        "absent",
        "ambiguous",
        "wrong_item",
        "unreviewed",
        "version_conflict",
        "scope_conflict",
        "reference_conflict",
    ],
)
def test_legacy_documentation_rejects_invalid_mapping_without_changes(scenario):
    # Preparar: una compra pagada con datos conocidos y texto aún ausente.
    owner = get_user_model().objects.create_user(username="legacy-invalid-owner")
    reviewer = get_user_model().objects.create_user(
        username="legacy-invalid-reviewer", is_staff=True
    )
    offer = create_available_offer()
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PAID,
        total_amount=Decimal("12.90"),
        currency="EUR",
    )
    item = OrderItem.objects.create(
        order=order,
        source_product=offer.product,
        product_sku="LEGACY-INVALID",
        product_name="Producto histórico",
        license_name="Licencia histórica",
        terms_version="1.0",
        usage_scope="Alcance histórico",
        price=Decimal("12.90"),
        currency="EUR",
    )
    LicenseGrant.objects.create(order_item=item)
    mapping = {
        "order_item_id": item.pk,
        "source_product_id": offer.product.pk,
        "source_license_type_id": offer.license_type.pk,
        "terms_version": "1.0",
        "terms_text": "Texto histórico documentado.",
        "usage_scope": "Alcance histórico",
        "grantor_name": "Concedente histórico",
        "rights_holder_name": "Titular histórico",
        "evidence_reference": "archivo-historico/revision-001",
        "reviewed_by_id": reviewer.pk,
        "reviewed_at": timezone.now(),
    }
    mappings = [mapping]

    # Preparar: introducir únicamente la incompatibilidad bajo prueba.
    if scenario == "absent":
        mappings = []
    elif scenario == "ambiguous":
        mappings = [mapping, dict(mapping)]
    elif scenario == "wrong_item":
        mapping["order_item_id"] = item.pk + 1
    elif scenario == "unreviewed":
        mapping["reviewed_by_id"] = owner.pk
    elif scenario == "version_conflict":
        mapping["terms_version"] = "2.0"
    elif scenario == "scope_conflict":
        mapping["usage_scope"] = "Otro alcance"
    elif scenario == "reference_conflict":
        other_type = LicenseType.objects.create(
            name="Otro tipo histórico",
            slug="otro-tipo-historico",
            usage_scope="Otro alcance",
            summary="Tipo distinto al propuesto por la correspondencia.",
            terms_version="1.0",
        )
        OrderItem.objects.filter(pk=item.pk).update(
            source_license_type_id=other_type.pk,
        )
        item.refresh_from_db()

    models = (
        Order,
        OrderItem,
        PaymentAttempt,
        LicenseGrant,
        Product,
        LicenseType,
        ProductLicenseOffer,
    )
    before = {
        model.__name__: list(model.objects.order_by("pk").values()) for model in models
    }

    # Actuar y comprobar: rechazar sin completar parcialmente la documentación.
    with pytest.raises(order_services.LegacyDocumentationConflict):
        order_services.regularize_legacy_order_item(
            order_item_id=item.pk, mappings=mappings
        )

    after = {
        model.__name__: list(model.objects.order_by("pk").values()) for model in models
    }
    assert after == before


@pytest.mark.django_db
def test_create_order_from_cart_captures_prepared_master_for_order_item(
    tmp_path,
    monkeypatch,
):
    # Preparar: aislar los archivos en almacenamiento temporal.
    monkeypatch.setattr(
        private_master_storage,
        "location",
        str(tmp_path / "private_media"),
    )

    owner = get_user_model().objects.create_user(
        username="prepared-master-buyer",
    )
    offer = create_available_offer(with_master=False)
    product = offer.product
    master_bytes = create_master_wav_bytes(sample_value=1)

    # Preparar: el servicio de carga recibe y prepara el archivo.
    preparation = set_product_master_audio(
        product_id=product.pk,
        uploaded_file=SimpleUploadedFile(
            "impacto.wav",
            master_bytes,
            content_type="audio/wav",
        ),
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )
    add_offer_to_cart(owner=owner, offer_id=offer.pk)

    # Actuar: crear el pedido desde el carrito.
    order = create_order_from_cart(owner=owner)

    # Comprobar: repcuperar los datos persistidos
    order.refresh_from_db()
    product.refresh_from_db()
    order_item = OrderItem.objects.get(order=order)
    captured_preparation = order_item.master_preparation

    assert captured_preparation is not None
    assert captured_preparation.pk == preparation.pk
    assert captured_preparation.storage_key == product.master_file.name
    assert MasterAudioPreparation.objects.count() == 1

    # La captura ocurre antes del pago y de la emisión del derecho.
    assert order.status == Order.Status.PENDING_PAYMENT
    assert not LicenseGrant.objects.filter(order_item=order_item).exists()


@pytest.mark.django_db
def test_order_item_preserves_captured_master_after_catalog_replacement(
    tmp_path,
    monkeypatch,
):
    # Preparar: aislar los archivos en almacenamiento temporal.
    monkeypatch.setattr(
        private_master_storage,
        "location",
        str(tmp_path / "private_media"),
    )

    owner = get_user_model().objects.create_user(username="historical-master-buyer")
    offer = create_available_offer(with_master=False)
    product = offer.product

    original_bytes = create_master_wav_bytes(sample_value=1)
    replacement_bytes = create_master_wav_bytes(sample_value=2)

    assert original_bytes != replacement_bytes

    # Preparar: asignar el maestro original
    original_preparation = set_product_master_audio(
        product_id=product.pk,
        uploaded_file=SimpleUploadedFile(
            "impacto.wav",
            original_bytes,
            content_type="audio/wav",
        ),
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )
    add_offer_to_cart(owner=owner, offer_id=offer.pk)

    # Preparar: crear el pedido que captura ese maestro.
    order = create_order_from_cart(owner=owner)
    order_item = OrderItem.objects.get(order=order)

    assert order_item.master_preparation == original_preparation

    original_line_values = OrderItem.objects.values().get(
        pk=order_item.pk,
    )

    # Actuar: sustituir el maestro del catálogo mediante el servicio.
    replacement_preparation = set_product_master_audio(
        product_id=product.pk,
        uploaded_file=SimpleUploadedFile(
            "impacto.wav",
            replacement_bytes,
            content_type="audio/wav",
        ),
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )

    # Comprobar: el producto apunta al nuevo maestro.
    product.refresh_from_db()
    order_item.refresh_from_db()

    assert product.master_file.name == replacement_preparation.storage_key
    assert replacement_preparation.pk != original_preparation.pk
    assert replacement_preparation.storage_key != original_preparation.storage_key
    assert MasterAudioPreparation.objects.count() == 2

    # Comprobar: la línea conserva su vínculo y todos sus datos históricos.
    assert order_item.master_preparation == original_preparation
    assert OrderItem.objects.values().get(pk=order_item.pk) == original_line_values

    # Comprobar: desde la línea seguimos llegando a los bytes originales.
    captured_preparation = order_item.master_preparation
    assert captured_preparation is not None

    with private_master_storage.open(
        captured_preparation.storage_key,
        "rb",
    ) as stored:
        assert stored.read() == original_bytes

    # El maestro actual del catálogo consitene los bytes de sustitución
    with private_master_storage.open(
        product.master_file.name,
        "rb",
    ) as stored:
        assert stored.read() == replacement_bytes
