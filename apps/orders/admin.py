"""Read-only administration for historical order operations."""

from django.contrib import admin

from .models import LicenseGrant, Order, OrderItem, PaymentAttempt


class HistoricalReadOnlyAdmin(admin.ModelAdmin):
    """Expose historical records without generic state-changing operations."""

    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        return {}


@admin.register(Order)
class OrderAdmin(HistoricalReadOnlyAdmin):
    list_display = (
        "id",
        "owner",
        "status",
        "total_amount",
        "currency",
        "created_at",
    )
    list_filter = ("status", "currency")
    search_fields = ("owner__username", "owner__email")
    ordering = ("-created_at", "-pk")
    list_per_page = 25
    list_select_related = ("owner",)
    readonly_fields = (
        "owner",
        "status",
        "total_amount",
        "currency",
        "created_at",
    )


@admin.register(OrderItem)
class OrderItemAdmin(HistoricalReadOnlyAdmin):
    list_display = (
        "id",
        "order",
        "product_sku",
        "product_name",
        "license_name",
        "terms_version",
        "price",
        "currency",
    )
    list_filter = ("terms_version", "currency")
    search_fields = (
        "product_sku",
        "product_name",
        "license_name",
        "order__owner__username",
    )
    ordering = ("-order__created_at", "-pk")
    list_per_page = 25
    list_select_related = (
        "order",
        "order__owner",
    )
    fields = (
        "order",
        "product_sku",
        "product_name",
        "license_name",
        "terms_version",
        "terms_text",
        "usage_scope",
        "grantor_name",
        "rights_holder_name",
        "price",
        "currency",
    )
    readonly_fields = fields


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(HistoricalReadOnlyAdmin):
    list_display = (
        "id",
        "order",
        "result",
        "amount",
        "currency",
        "created_at",
    )
    list_filter = ("result", "currency")
    search_fields = (
        "order__owner__username",
        "order__owner__email",
    )
    ordering = ("-created_at", "-pk")
    list_per_page = 25
    list_select_related = (
        "order",
        "order__owner",
    )
    fields = (
        "order",
        "result",
        "amount",
        "currency",
        "created_at",
    )
    readonly_fields = fields


@admin.register(LicenseGrant)
class LicenseGrantAdmin(HistoricalReadOnlyAdmin):
    list_display = (
        "id",
        "order_item",
        "status",
        "issued_at",
    )
    list_filter = ("status",)
    search_fields = (
        "order_item__product_name",
        "order_item__product_sku",
        "order_item__license_name",
        "order_item__order__owner__username",
    )
    ordering = ("-issued_at", "-pk")
    list_per_page = 25
    list_select_related = (
        "order_item",
        "order_item__order",
        "order_item__order__owner",
    )
    fields = (
        "order_item",
        "status",
        "issued_at",
    )
    readonly_fields = fields
