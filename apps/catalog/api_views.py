from urllib.parse import urlencode

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.catalog.selectors import (
    ORDERING_OPTIONS,
    get_active_categories,
    get_active_license_types,
    get_available_products,
)
from apps.catalog.serializers import (
    PublicProductDetailSerializer,
    PublicProductListSerializer,
)


class PageNotFound(NotFound):
    pass


class PublicProductPagination(PageNumberPagination):
    page_size = 12

    def paginate_queryset(self, queryset, request, view=None):
        self.request_path = request.path
        self.query_params = view.get_canonical_query_params()
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound as error:
            raise PageNotFound from error

    def get_next_link(self):
        if not self.page.has_next():
            return None
        return self.get_page_link(self.page.next_page_number())

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        return self.get_page_link(self.page.previous_page_number())

    def get_page_link(self, page_number):
        return f"{self.request_path}?{urlencode({**self.query_params, 'page': page_number})}"


class PublicCatalogAPIView:
    def error_response(
        self, code, parameter=None, status_code=status.HTTP_400_BAD_REQUEST
    ):
        error = {"code": code}
        if parameter:
            error["parameter"] = parameter
        return Response({"error": error}, status=status_code)

    def http_method_not_allowed(self, request, *args, **kwargs):
        return self.error_response(
            "method_not_allowed",
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def handle_exception(self, error):
        if isinstance(error, PageNotFound):
            return self.error_response(
                "page_not_found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if isinstance(error, Http404):
            return self.error_response(
                "product_not_found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return super().handle_exception(error)


class PublicProductListView(PublicCatalogAPIView, ListAPIView):
    serializer_class = PublicProductListSerializer
    pagination_class = PublicProductPagination
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        query_error = self.get_query_error()
        if query_error:
            return query_error
        return super().get(request, *args, **kwargs)

    def get_query_error(self):
        search_query = " ".join(self.request.query_params.get("q", "").split())
        category_slug = self.request.query_params.get("category", "")
        license_slug = self.request.query_params.get("license", "")
        ordering = self.request.query_params.get("ordering", "")
        if len(search_query) > 100:
            return self.error_response("invalid_query_parameter", "q")
        if (
            category_slug
            and not get_active_categories().filter(slug=category_slug).exists()
        ):
            return self.error_response("invalid_query_parameter", "category")
        if (
            license_slug
            and not get_active_license_types().filter(slug=license_slug).exists()
        ):
            return self.error_response("invalid_query_parameter", "license")
        if ordering and ordering not in ORDERING_OPTIONS:
            return self.error_response("invalid_query_parameter", "ordering")
        return None

    def get_canonical_query_params(self):
        search_query = " ".join(self.request.query_params.get("q", "").split())
        query_params = {}
        if search_query:
            query_params["q"] = search_query
        for parameter in ("category", "license", "ordering"):
            value = self.request.query_params.get(parameter, "")
            if value:
                query_params[parameter] = value
        return query_params

    def get_queryset(self):
        return get_available_products(
            search_query=" ".join(self.request.query_params.get("q", "").split()),
            category_slug=self.request.query_params.get("category", ""),
            license_slug=self.request.query_params.get("license", ""),
            ordering=self.request.query_params.get("ordering", ""),
        )


class PublicProductDetailView(PublicCatalogAPIView, RetrieveAPIView):
    serializer_class = PublicProductDetailSerializer
    lookup_field = "slug"
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return get_available_products()
