from urllib.parse import urlencode

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from apps.catalog.selectors import (
    ORDERING_OPTIONS,
    get_active_categories,
    get_active_license_types,
    get_available_products,
)


def product_list(request):
    search_query = " ".join(request.GET.get("q", "").split())
    category_slug = request.GET.get("category", "")
    license_slug = request.GET.get("license", "")
    ordering = request.GET.get("ordering", "")
    if len(search_query) > 100:
        return HttpResponseBadRequest("Parámetro q demasiado largo.")
    if (
        category_slug
        and not get_active_categories().filter(slug=category_slug).exists()
    ):
        return HttpResponseBadRequest("Parámetro category no reconocido.")
    if (
        license_slug
        and not get_active_license_types().filter(slug=license_slug).exists()
    ):
        return HttpResponseBadRequest("Parámetro license no reconocido.")
    if ordering and ordering not in ORDERING_OPTIONS:
        return HttpResponseBadRequest("Parámetro ordering no reconocido.")
    products_queryset = get_available_products(
        search_query=search_query,
        category_slug=category_slug,
        license_slug=license_slug,
        ordering=ordering,
    )
    paginator = Paginator(products_queryset, 12)
    try:
        products = paginator.page(request.GET.get("page", 1))
    except (EmptyPage, PageNotAnInteger) as error:
        raise Http404 from error
    # Only q, category, license and ordering survive a page change.
    preserved_params = {}
    if search_query:
        preserved_params["q"] = search_query
    if category_slug:
        preserved_params["category"] = category_slug
    if license_slug:
        preserved_params["license"] = license_slug
    if ordering:
        preserved_params["ordering"] = ordering
    return render(
        request,
        "catalog/product_list.html",
        {
            "products": products,
            "preserved_query_string": urlencode(preserved_params),
            "search_query": search_query,
            "category_slug": category_slug,
            "license_slug": license_slug,
            "ordering": ordering,
            "categories": get_active_categories(),
            "license_types": get_active_license_types(),
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(get_available_products(), slug=slug)
    product_context = {
        "name": product.name,
        "category_name": product.category.name,
        "description": product.description,
        "duration_ms": product.duration_ms,
        "audio_format": product.get_audio_format_display(),
        "sample_rate_hz": product.sample_rate_hz,
        "bit_depth": product.bit_depth,
        "preview_available": bool(product.preview_file),
        "preview_url": product.preview_file.url if product.preview_file else "",
        "license_offers": [
            {
                "name": offer.license_type.name,
                "usage_scope": offer.license_type.usage_scope,
                "summary": offer.license_type.summary,
                "price": offer.price,
                "currency": offer.currency,
            }
            for offer in product.license_offers.all()
        ],
    }
    return render(
        request,
        "catalog/product_detail.html",
        {"product_detail": product_context},
    )
