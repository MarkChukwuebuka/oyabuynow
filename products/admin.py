from django.contrib import admin

from crm.admin import BaseAdmin
from products.models import Tag, Category, Product, DealOfTheDay, ProductReview


# Register your models here.
@admin.register(Tag)
class TagAdmin(BaseAdmin):
    list_display = ["id", "name"] + BaseAdmin.list_display
    search_fields = ["name"]


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ["id", "name"] + BaseAdmin.list_display
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ["name", "id", "price", "availability"
                    ] + BaseAdmin.list_display
    search_fields = ["name", "description"]
    list_filter = ["rating", "price"]


@admin.register(DealOfTheDay)
class DealOfTheDayAdmin(BaseAdmin):
    list_display = ['product', 'discount_percentage', 'start_time', 'end_time', 'is_active']
    list_filter = ['is_active', 'start_time', 'end_time']
    search_fields = ['product__name',]


@admin.register(ProductReview)
class ProductReviewAdmin(BaseAdmin):
    list_display = ['product', 'rating', 'user', 'review', 'created_at']
    list_filter = ['rating', 'user']
    search_fields = ['product__name', 'review']
