from django.contrib import admin

from crm.admin import BaseAdmin
from payments.models import Order, OrderItem, Payment, BankAccount


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = [
        "user", "email", "total_cost", "paid", "status"
    ]
    search_fields = ["address", "email", "state", "first_name", "ref"]
    list_filter = ["status", "paid"]



@admin.register(OrderItem)
class OrderItemAdmin(BaseAdmin):
    list_display = [
        "order", "product", "quantity", "price"
    ]
    search_fields = ["price",]
    list_filter = ["product"]


@admin.register(Payment)
class PaymentAdmin(BaseAdmin):
    list_display = [
        "user", "amount", "ref", "verified"
    ]
    search_fields = ["amount", "ref"]
    list_filter = ["verified"]


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        "bank_name", "account_number", "account_name"
    ]

