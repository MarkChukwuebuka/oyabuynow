from rest_framework import serializers

from products.models import Product
from products.services.category_brand_service import BrandService, CategoryService, TagService, SubcategoryService, \
    ColorService


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id", "name", "price", "percentage_discount", "sku", "description", "stock", "availability",
            "rating", "discounted_price", "categories", "tags", "colors",
        ]


class CreateProductSerializer(serializers.Serializer):

    name = serializers.CharField(required=True)
    price = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    percentage_discount = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    cost_price = serializers.IntegerField(required=False, allow_null=True)
    stock = serializers.IntegerField(required=False, allow_null=True)
    weight = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    dimensions = serializers.CharField(required=False, allow_null=True)
    brand_id = serializers.IntegerField(required=False, allow_null=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    free_shipping = serializers.BooleanField(required=False, default=False)
    short_description = serializers.CharField(required=False, allow_null=True)
    tag_ids = serializers.ListSerializer(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    color_ids = serializers.ListSerializer(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    subcategory_ids = serializers.ListSerializer(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    media = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True
    )

    def validate(self, attrs):
        data = attrs.copy()

        request = self.context.get("request")
        if data.get("brand_id"):
            brand_service = BrandService(request)
            brand, error = brand_service.fetch_single_by_id(data.get("brand_id"))
            if error:
                raise serializers.ValidationError(error, code="brand_id")
            data["brand"] = brand

        if data.get("category_id"):
            category_service = CategoryService(request)
            category, error = category_service.fetch_single_by_id(data.get("category_id"))
            if error:
                raise serializers.ValidationError(error, code="category_id")
            data["category"] = category

        if data.get("tag_ids"):
            tag_service = TagService(request)
            tags = tag_service.fetch_by_ids(data.get("tag_ids"))
            data["tags"] = tags

        if data.get("subcategory_ids"):
            subcategory_service = SubcategoryService(request)
            subcategories = subcategory_service.fetch_by_ids(data.get("subcategory_ids"))
            data["subcategories"] = subcategories

        if data.get("color_ids"):
            color_service = ColorService(request)
            colors = color_service.fetch_by_ids(data.get("color_ids"))
            data["colors"] = colors

        return data