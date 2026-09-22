from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.orders.models import Order, OrderItem
from apps.orders.selectors import get_order_for_owner, get_orders_for_owner


def create_user(username):
    return get_user_model().objects.create_user(
        username=username,
        password="ReliablePassword123!",
    )


@pytest.mark.django_db
def test_get_orders_for_owner_returns_only_owner_orders_ordered_by_created_at_and_id():
    owner = create_user("orders-selector-owner")
    other_user = create_user("orders-selector-other")

    older_order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("10.00"),
    )
    newer_order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("20.00"),
    )
    other_order = Order.objects.create(
        owner=other_user,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("30.00"),
    )

    older_order.created_at = timezone.datetime(
        2026,
        9,
        22,
        10,
        0,
        tzinfo=timezone.get_current_timezone(),
    )
    newer_order.created_at = timezone.datetime(
        2026,
        9,
        22,
        11,
        0,
        tzinfo=timezone.get_current_timezone(),
    )
    other_order.created_at = timezone.datetime(
        2026,
        9,
        22,
        12,
        0,
        tzinfo=timezone.get_current_timezone(),
    )
    Order.objects.bulk_update(
        [older_order, newer_order, other_order],
        ["created_at"],
    )

    orders = list(get_orders_for_owner(owner=owner))

    assert orders == [newer_order, older_order]


@pytest.mark.django_db
def test_get_order_for_owner_returns_own_order_with_items():
    owner = create_user("order-detail-owner")
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
    )
    OrderItem.objects.create(
        order=order,
        product_sku="PED-001",
        product_name="Impacto cinematográfico",
        license_name="Licencia de pedido",
        terms_version="1.0",
        price=Decimal("12.90"),
    )

    selected_order = get_order_for_owner(owner=owner, order_id=order.pk)

    assert selected_order == order
    assert OrderItem.objects.get(order=selected_order).product_sku == "PED-001"


@pytest.mark.django_db
def test_get_order_for_owner_does_not_return_another_users_order():
    owner = create_user("order-detail-owner-private")
    other_user = create_user("order-detail-other-private")
    other_order = Order.objects.create(
        owner=other_user,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=Decimal("12.90"),
    )

    with pytest.raises(Order.DoesNotExist):
        get_order_for_owner(owner=owner, order_id=other_order.pk)
