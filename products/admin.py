from django.contrib import admin

from crm.admin import BaseAdmin
from media.admin import UploadInline
from products.models import Tag, Category, Product, ProductReview, Subcategory


# Register your models here.
@admin.register(Tag)
class TagAdmin(BaseAdmin):
    list_display = ["id", "name"] + BaseAdmin.list_display
    search_fields = ["name"]


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ["id", "name"] + BaseAdmin.list_display
    search_fields = ["name"]

@admin.register(Subcategory)
class SubcategoryAdmin(BaseAdmin):
    list_display = ["id", "name", "category"] + BaseAdmin.list_display
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ["id", "name", "price", "availability"
                    ] + BaseAdmin.list_display
    search_fields = ["name", "description", "price", "sku"]
    list_filter = ["rating", "price"]

    inlines = [UploadInline]


@admin.register(ProductReview)
class ProductReviewAdmin(BaseAdmin):
    list_display = ['product', 'rating', 'user', 'review', 'created_at']
    list_filter = ['rating', 'user']
    search_fields = ['product__name', 'review']
