from rest_framework import serializers


class PublicCategorySerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.SlugField()


class PublicLicenseSerializer(serializers.Serializer):
    name = serializers.CharField(source="license_type.name")
    slug = serializers.SlugField(source="license_type.slug")
    usage_scope = serializers.CharField(source="license_type.usage_scope")
    summary = serializers.CharField(source="license_type.summary")


class PublicProductListSerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.SlugField()
    summary = serializers.CharField()
    category = PublicCategorySerializer()
    duration_ms = serializers.IntegerField()
    audio_format = serializers.CharField()
    sample_rate_hz = serializers.IntegerField()
    bit_depth = serializers.IntegerField()
    minimum_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    currency = serializers.CharField(default="EUR")
    licenses = PublicLicenseSerializer(
        source="license_offers",
        many=True,
        read_only=True,
    )
    detail_url = serializers.SerializerMethodField()

    def get_detail_url(self, product):
        return f"/api/v1/catalog/products/{product.slug}/"


class PublicProductLicenseOfferSerializer(serializers.Serializer):
    license = PublicLicenseSerializer(source="*")
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()


class PublicProductDetailSerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.SlugField()
    summary = serializers.CharField()
    category = PublicCategorySerializer()
    duration_ms = serializers.IntegerField()
    audio_format = serializers.CharField()
    sample_rate_hz = serializers.IntegerField()
    bit_depth = serializers.IntegerField()
    minimum_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    currency = serializers.CharField(default="EUR")
    description = serializers.CharField()
    preview_url = serializers.SerializerMethodField()
    license_offers = PublicProductLicenseOfferSerializer(many=True, read_only=True)
    detail_url = serializers.SerializerMethodField()

    def get_preview_url(self, product):
        if not product.preview_file:
            return None
        return product.preview_file.url

    def get_detail_url(self, product):
        return f"/api/v1/catalog/products/{product.slug}/"
