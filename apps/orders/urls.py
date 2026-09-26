from django.urls import path

from . import views

app_name = "orders"
urlpatterns = [
    path("", views.order_list, name="list"),
    path("<int:order_id>/", views.order_detail, name="detail"),
    path("create/", views.create_order, name="create"),
]
