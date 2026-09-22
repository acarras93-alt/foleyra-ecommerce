from django.db.models import QuerySet

from apps.orders.models import Order


def get_orders_for_owner(*, owner) -> QuerySet[Order]:
    return Order.objects.filter(owner=owner).order_by("-created_at", "-id")


def get_order_for_owner(*, owner, order_id: int) -> Order:
    return Order.objects.filter(owner=owner).prefetch_related("items").get(pk=order_id)
