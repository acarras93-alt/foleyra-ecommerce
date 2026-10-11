"""URL configuration for the Foleyra project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.orders import views as order_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.users.urls")),
    path("cart/", include("apps.cart.urls")),
    path("orders/", include("apps.orders.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("api/v1/catalog/", include("apps.catalog.api_urls")),
    path("", include("apps.core.urls")),
    path("licenses/", order_views.license_list, name="license_list"),
    path(
        "licenses/<int:license_id>/",
        order_views.license_detail,
        name="license_detail",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
