from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render

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
