from django.contrib import admin
from django.utils.html import format_html

from accounts.models import User, VendorProfile
from crm.admin import BaseAdmin


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User



class CustomUserCreationForm(UserCreationForm):
    """Custom form for creating users"""

    class Meta:
        model = User
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):
    """Custom form for changing users"""

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'is_active', 'is_staff')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin interface for User model"""
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'address')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "user", "status", "business_phone", "logo_thumbnail")
    list_filter = ("status",)
    search_fields = ("business_name", "user__username", "user__email", "business_phone")

    # ✅ Declare computed fields as readonly
    readonly_fields = (
        "get_user_fullname",
        "get_user_email",
        "logo_preview",
        "id_card_preview",
        "profile_photo_preview",
    )

    fieldsets = (
        ("User Information", {
            "fields": (
                "user",
                ("get_user_fullname", "get_user_email"),
            ),
        }),
        ("Business Information", {
            "fields": (
                "business_name",
                "store_name",
                "business_phone",
                "business_email",
                "business_address",
                "bank_name",
                "account_number",
                "status",
                "rating"
            ),
        }),
        ("Media Uploads", {
            "fields": (
                "business_logo",
                "logo_preview",
                "id_card",
                "id_card_preview",
                "profile_photo",
                "profile_photo_preview",
            ),
        }),
    )

    # --- Related User Info ---
    @admin.display(description="Full Name")
    def get_user_fullname(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else "-"

    @admin.display(description="User Email")
    def get_user_email(self, obj):
        return obj.user.email if obj.user else "-"

    # --- Thumbnails ---
    @admin.display(description="Logo Thumbnail")
    def logo_thumbnail(self, obj):
        if obj.business_logo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:5px;object-fit:cover;" />',
                obj.business_logo.url,
            )
        return "—"

    def logo_preview(self, obj):
        if obj.business_logo:
            return format_html(
                '<img src="{}" width="150" style="border-radius:8px;object-fit:cover;" />',
                obj.business_logo.url,
            )
        return "No logo uploaded"

    def id_card_preview(self, obj):
        if obj.id_card:
            return format_html(
                '<img src="{}" width="150" style="border-radius:8px;object-fit:cover;" />',
                obj.id_card.url,
            )
        return "No ID card uploaded"

    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" width="150" style="border-radius:8px;object-fit:cover;" />',
                obj.profile_photo.url,
            )
        return "No profile photo uploaded"