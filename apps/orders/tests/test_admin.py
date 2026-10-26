from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.catalog.models import MasterAudioPreparation
from apps.orders.models import LicenseGrant, Order, OrderItem, PaymentAttempt

HISTORICAL_MODELS = (Order, OrderItem, PaymentAttempt, LicenseGrant)


def grant_view_permissions(user):
    permissions = []
    for model in HISTORICAL_MODELS:
        content_type = ContentType.objects.get_for_model(model)
        permissions.append(
            Permission.objects.get(
                content_type=content_type,
                codename=f"view_{model._meta.model_name}",
            )
        )
    user.user_permissions.add(*permissions)


def create_support_user():
    user = get_user_model().objects.create_user(
        username="operations-support",
        password="ReliablePassword123!",
        is_staff=True,
    )
    grant_view_permissions(user)
    return user


def create_historical_data(*, suffix=""):
    owner = get_user_model().objects.create_user(
        username=f"buyer-{suffix or 'base'}",
        email=f"buyer-{suffix or 'base'}@example.test",
    )
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PAID,
        total_amount=Decimal("12.90"),
    )
    preparation = MasterAudioPreparation.objects.create(
        storage_key=f"masters/private-history-{suffix or 'base'}.wav",
        sha256="a" * 64,
        size_bytes=1234,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    item = OrderItem.objects.create(
        order=order,
        master_preparation=preparation,
        product_sku=f"HIST-{suffix or 'BASE'}",
        product_name=f"Paisaje histórico {suffix}".strip(),
        license_name="Licencia audiovisual",
        terms_version="1.0",
        terms_text="Condiciones históricas.",
        usage_scope="Una producción",
        grantor_name="Foleyra",
        rights_holder_name="Foleyra",
        price=Decimal("12.90"),
    )
    attempt = PaymentAttempt.objects.create(
        order=order,
        idempotency_key=uuid4(),
        result=PaymentAttempt.Result.APPROVED,
        amount=order.total_amount,
        currency=order.currency,
    )
    grant = LicenseGrant.objects.create(
        order_item=item,
        status=LicenseGrant.Status.ACTIVE,
    )
    return order, item, attempt, grant, preparation


@pytest.mark.django_db
def test_support_can_consult_historical_models_but_cannot_write(client):
    order, item, attempt, grant, _ = create_historical_data()
    user = create_support_user()
    client.force_login(user)

    objects = (
        ("orders_order", order),
        ("orders_orderitem", item),
        ("orders_paymentattempt", attempt),
        ("orders_licensegrant", grant),
    )
    for model_name, obj in objects:
        changelist = client.get(reverse(f"admin:{model_name}_changelist"))
        change = client.get(reverse(f"admin:{model_name}_change", args=[obj.pk]))
        post = client.post(
            reverse(f"admin:{model_name}_change", args=[obj.pk]),
            {"_save": "Guardar"},
        )
        assert changelist.status_code == 200
        assert change.status_code == 200
        assert post.status_code == 403

    order.refresh_from_db()
    attempt.refresh_from_db()
    grant.refresh_from_db()
    assert order.status == Order.Status.PAID
    assert attempt.result == PaymentAttempt.Result.APPROVED
    assert grant.status == LicenseGrant.Status.ACTIVE


@pytest.mark.django_db
def test_historical_admin_rejects_add_delete_and_bulk_actions(client):
    order, item, attempt, grant, _ = create_historical_data()
    user = create_support_user()
    client.force_login(user)

    objects = (
        ("orders_order", order),
        ("orders_orderitem", item),
        ("orders_paymentattempt", attempt),
        ("orders_licensegrant", grant),
    )
    for model_name, obj in objects:
        add_response = client.get(reverse(f"admin:{model_name}_add"))
        delete_response = client.get(
            reverse(f"admin:{model_name}_delete", args=[obj.pk]),
        )
        changelist = client.get(reverse(f"admin:{model_name}_changelist"))
        content = changelist.content.decode()
        assert add_response.status_code == 403
        assert delete_response.status_code == 403
        assert "delete_selected" not in content


@pytest.mark.django_db
def test_historical_admin_does_not_expose_payment_keys_or_master_storage_keys(
    client,
):
    order, item, attempt, _, preparation = create_historical_data()
    user = create_support_user()
    client.force_login(user)

    payment_key = str(attempt.idempotency_key)
    payment_list = client.get(reverse("admin:orders_paymentattempt_changelist"))
    payment_change = client.get(
        reverse("admin:orders_paymentattempt_change", args=[attempt.pk]),
    )
    item_list = client.get(reverse("admin:orders_orderitem_changelist"))
    item_change = client.get(
        reverse("admin:orders_orderitem_change", args=[item.pk]),
    )

    assert payment_key not in payment_list.content.decode()
    assert payment_key not in payment_change.content.decode()
    assert preparation.storage_key not in item_list.content.decode()
    assert preparation.storage_key not in item_change.content.decode()
    assert str(order.pk) in item_list.content.decode()


@pytest.mark.django_db
def test_order_admin_list_eager_loads_owner_without_n_plus_one(client):
    for number in range(3):
        create_historical_data(suffix=f"query-{number}")
    user = create_support_user()
    client.force_login(user)

    with CaptureQueriesContext(connection) as queries:
        response = client.get(reverse("admin:orders_order_changelist"))

    assert response.status_code == 200
    assert len(queries) < 15
