# apps/catalog/models.py
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, router, transaction
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


class MasterAudioPreparation(models.Model):
    storage_key = models.CharField(max_length=500, unique=True)
    sha256 = models.CharField(max_length=64)
    size_bytes = models.PositiveBigIntegerField()
    audio_format = models.CharField(
        max_length=8,
        choices=Product.AudioFormat.choices,
    )
    sample_rate_hz = models.PositiveIntegerField()
    bit_depth = models.PositiveSmallIntegerField()
    prepared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(sample_rate_hz__gte=48_000),
                name="prepared_master_min_sample_rate",
            ),
            models.CheckConstraint(
                condition=Q(bit_depth__gte=24),
                name="prepared_master_min_bit_depth",
            ),
            models.CheckConstraint(
                condition=Q(size_bytes__gt=0),
                name="prepared_master_nonempty_file",
            ),
            models.CheckConstraint(
                condition=Q(audio_format__in=Product.AudioFormat.values),
                name="prepared_master_allowed_format",
            ),
        ]


class LicenseType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=130, unique=True)
    usage_scope = models.CharField(max_length=180)
    summary = models.CharField(max_length=255)
    terms_version = models.CharField(max_length=20)
    terms_text = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "pk"]  # noqa: RUF012

    def save(
        self,
        *,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        database = using or router.db_for_write(type(self), instance=self)

        if update_fields is not None:
            update_fields = frozenset(update_fields)
            if not update_fields:
                return

        with transaction.atomic(using=database):
            previous = None

            if self.pk is not None:
                previous = (
                    type(self)
                    .objects.using(database)
                    .select_for_update()
                    .filter(pk=self.pk)
                    .values("terms_text", "usage_scope", "terms_version")
                    .first()
                )

            if previous is not None:
                # Comparar únicamente los campos que se van a guardar.
                content_changed = any(
                    (update_fields is None or field in update_fields)
                    and getattr(self, field) != previous[field]
                    for field in ("terms_text", "usage_scope")
                )

                # Cambiar la versión en memoria no basta:
                # también debe incluirse entre los campos guardados.
                saved_version = previous["terms_version"]
                if update_fields is None or "terms_version" in update_fields:
                    saved_version = self.terms_version

                if content_changed and (
                    not saved_version.strip()
                    or saved_version.strip() == previous["terms_version"].strip()
                ):
                    raise ValidationError(
                        {
                            "terms_version": (
                                "Debes indicar una nueva versión al cambiar "
                                "el texto o el alcance de las condiciones."
                            )
                        }
                    )

            return super().save(
                force_insert=force_insert,
                force_update=force_update,
                using=database,
                update_fields=update_fields,
            )

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
