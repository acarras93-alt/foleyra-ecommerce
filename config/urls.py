"""URL configuration for the Foleyra project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("catalog/", include("apps.catalog.urls")),
    path("", include("apps.core.urls")),
]
