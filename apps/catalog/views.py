from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import Http404
from django.shortcuts import render

from apps.catalog.selectors import get_available_products


def product_list(request):
    paginator = Paginator(get_available_products(), 12)
    try:
        products = paginator.page(request.GET.get("page", 1))
    except (EmptyPage, PageNotAnInteger) as error:
        raise Http404 from error
    return render(
        request,
        "catalog/product_list.html",
        {"products": products},
    )
