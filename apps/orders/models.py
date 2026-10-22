from django.conf import settings
from django.db import models


class Order(models.Model):
    """Represent a customer's historical order, including its payment status,
    total amount, currency, and creation date.
    """

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAID = "paid", "Paid"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    """Store the product, license, terms version, and price captured when an
    order is created, preserving those values independently of catalog changes.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    source_product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="orders_items",
        null=True,
        blank=True,
    )
    source_license_type = models.ForeignKey(
        "catalog.LicenseType",
        on_delete=models.PROTECT,
        related_name="order_items",
        null=True,
        blank=True,
    )
    master_preparation = models.ForeignKey(
        "catalog.MasterAudioPreparation",
        on_delete=models.PROTECT,
        related_name="order_items",
        null=True,
        blank=True,
    )

    product_sku = models.CharField(max_length=40)
    product_name = models.CharField(max_length=140)
    license_name = models.CharField(max_length=120)
    terms_version = models.CharField(max_length=20)
    terms_text = models.TextField(blank=True, default="")
    usage_scope = models.CharField(
        max_length=180,
        blank=True,
        default="",
    )
    grantor_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )
    rights_holder_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR", editable=False)


class LicenseGrant(models.Model):
    """Represent a usage right granted for a single order item after payment
    approval, with its status and issue date.

    The owner is determined through the related order item and order.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"

    order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.PROTECT,
        related_name="license_grant",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    issued_at = models.DateTimeField(auto_now_add=True)


class PaymentAttempt(models.Model):
    """Record the result, amount, currency, and date of a simulated payment
    attempt for an order.

    The idempotency key identifies repeated requests for the same attempt
    within that order.
    """

    class Result(models.TextChoices):
        APPROVED = "approved", "Approved"
        FAILED = "failed", "Failed"

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="payment_attempts",
    )
    idempotency_key = models.UUIDField()
    result = models.CharField(
        max_length=10,
        choices=Result.choices,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)
