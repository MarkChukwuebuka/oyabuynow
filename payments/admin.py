from django.contrib import admin

from crm.admin import BaseAdmin
from payments.models import Order, OrderItem, Transaction


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = [
        "user", "email", "total_cost", "payment_status", "overall_status"
    ]
    search_fields = ["address", "email", "state", "first_name", "ref"]
    list_filter = ["overall_status", "payment_status"]



@admin.register(OrderItem)
class OrderItemAdmin(BaseAdmin):
    list_display = [
        "order", "product", "quantity", "price", "status"
    ]
    search_fields = ["price",]
    list_filter = ["product"]


@admin.register(Transaction)
class TransactionAdmin(BaseAdmin):
    list_display = [
        "order", "amount", "reference", "status"
    ]
    search_fields = ["reference", ]
    list_filter = ["reference", "status"]

