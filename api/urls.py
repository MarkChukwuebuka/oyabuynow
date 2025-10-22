from django.urls import path
from accounts.views import check_email, get_banks, verify_bank_account, ResendOTPView
from media.views import delete_product_image
from products.views import get_subcategories

urlpatterns = [
    path("check-email/", check_email, name="check_email"),
    path("get-banks/", get_banks, name="get-banks"),
    path("verify-bank-account/", verify_bank_account, name="verify-bank-account"),
    path("get-subcategories/<int:category_id>/", get_subcategories, name='get-subcategories'),
    path("delete-product-image/<int:upload_id>/", delete_product_image, name='delete-product-image'),
    path("resend-otp/", ResendOTPView.as_view(), name='resend-otp'),
]
