from django.urls import path

from . import api_views

app_name = "catalog_api"

urlpatterns = [
    path("products/", api_views.PublicProductListView.as_view(), name="product-list"),
    path(
        "products/<slug:slug>/",
        api_views.PublicProductDetailView.as_view(),
        name="product-detail",
    ),
]
