from django import forms
from django.contrib import admin

from .models import (
    Category,
    LicenseType,
    Product,
    ProductLicenseOffer,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_display_links = ("name",)
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("name", "pk")
    list_per_page = 25
    prepopulated_fields = {"slug": ("name",)}  # noqa: RUF012

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "audio_format",
        "is_active",
    )
    list_display_links = ("name",)
    list_filter = ("is_active", "category", "audio_format")
    search_fields = ("name", "sku", "slug")
    ordering = ("name", "pk")
    list_per_page = 25

    list_select_related = ("category",)

    fields = (
        "category",
        "name",
        "slug",
        "sku",
        "summary",
        "description",
        "duration_ms",
        "audio_format",
        "sample_rate_hz",
        "bit_depth",
        "preview_file",
        "is_active",
    )

    def has_delete_permission(self, request, obj=None):
        return False


class LicenseTypeAdminForm(forms.ModelForm):
    class Meta:
        model = LicenseType
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        if not self.instance.pk:
            return cleaned_data

        previous = (
            LicenseType.objects.filter(pk=self.instance.pk)
            .values(
                "terms_text",
                "usage_scope",
                "terms_version",
            )
            .first()
        )

        if previous is None:
            return cleaned_data

        fields = ("terms_text", "usage_scope", "terms_version")

        if any(field not in cleaned_data for field in fields):
            return cleaned_data

        content_changed = any(
            cleaned_data[field] != previous[field]
            for field in ("terms_text", "usage_scope")
        )

        new_version = cleaned_data["terms_version"].strip()
        old_version = previous["terms_version"].strip()

        if content_changed and (not new_version or new_version == old_version):
            self.add_error(
                "terms_version",
                "Debes indicar una nueva versión al cambiar "
                "las condiciones de la licencia.",
            )

        return cleaned_data


@admin.register(LicenseType)
class LicenseTypeAdmin(admin.ModelAdmin):
    form = LicenseTypeAdminForm

    list_display = (
        "name",
        "slug",
        "terms_version",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "usage_scope")
    ordering = ("name", "pk")
    list_per_page = 25

    prepopulated_fields = {"slug": ("name",)}  # noqa: RUF012

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductLicenseOffer)
class ProductLicenseOfferAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "license_type",
        "price",
        "is_active",
    )
    list_filter = (
        "is_active",
        "product__category",
        "license_type",
    )
    search_fields = (
        "product__name",
        "product__sku",
        "license_type__name",
    )
    ordering = ("price", "pk")
    list_per_page = 25

    list_select_related = ("product", "license_type")

    def has_delete_permission(self, request, obj=None):
        return False
