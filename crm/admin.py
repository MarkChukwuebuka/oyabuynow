from django.contrib import admin

from crm.models import Color


class BaseAdmin(admin.ModelAdmin):
    list_display = ["created_at"]
    list_filter = []
    date_hierarchy = "created_at"


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_code']
    list_filter = ['name', 'hex_code']
    search_fields = ['name', 'hex_code']