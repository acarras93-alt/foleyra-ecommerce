import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.orders.models import Order


@pytest.mark.django_db
def test_order_records_creation_datetime():
    owner = get_user_model().objects.create_user(
        username="created-at-order-owner",
        password="ReliablePassword123!",
    )

    before_creation = timezone.now()
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount="12.90",
    )
    after_creation = timezone.now()

    assert order.created_at is not None
    assert before_creation <= order.created_at <= after_creation
