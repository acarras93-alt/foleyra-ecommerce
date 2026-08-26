from django.shortcuts import render

from apps.catalog.selectors import get_available_products


def product_list(request):
    return render(
        request,
        "catalog/product_list.html",
        {"products": get_available_products()},
    )
