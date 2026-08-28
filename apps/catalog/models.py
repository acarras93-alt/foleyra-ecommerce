# apps/catalog/models.py
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.catalog.storage import PreviewStorage, PrivateMasterStorage

preview_storage = PreviewStorage()
private_master_storage = PrivateMasterStorage()


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "pk"]  # noqa: RUF012
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    class AudioFormat(models.TextChoices):
        WAV = "wav", "WAV"
        FLAC = "flac", "FLAC"
        AIFF = "aiff", "AIFF"

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True)
    sku = models.CharField(max_length=40, unique=True)
    summary = models.CharField(max_length=255)
    description = models.TextField()
    duration_ms = models.PositiveIntegerField()
    audio_format = models.CharField(max_length=8, choices=AudioFormat.choices)
    sample_rate_hz = models.PositiveIntegerField()
    bit_depth = models.PositiveSmallIntegerField()
    preview_file = models.FileField(
        upload_to="previews/",
        storage=preview_storage,
        blank=True,
    )
    master_file = models.FileField(
        upload_to="masters/",
        storage=private_master_storage,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "pk"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} ({self.sku})"


class LicenseType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=130, unique=True)
    usage_scope = models.CharField(max_length=180)
    summary = models.CharField(max_length=255)
    terms_version = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "pk"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} (v{self.terms_version})"


class ProductLicenseOffer(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="license_offers",
    )
    license_type = models.ForeignKey(
        LicenseType,
        on_delete=models.PROTECT,
        related_name="product_offers",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    currency = models.CharField(max_length=3, default="EUR", editable=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["product", "license_type"],
                name="uniq_product_license_offer",
            ),
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="product_license_price_nonnegative",
            ),
        ]
        ordering = ["price", "pk"]  # noqa: RUF012

    def __str__(self):
        return f"{self.product} — {self.license_type}"
