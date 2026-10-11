"""Define URL routes for cart display and item management."""

from django.urls import path

from . import views

app_name = "cart"
urlpatterns = [
    path("", views.cart_detail, name="detail"),
    path("items/add/", views.add_item, name="add-item"),
    path("items/<int:item_id>/remove/", views.remove_item, name="remove-item"),
]
