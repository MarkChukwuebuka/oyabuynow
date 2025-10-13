from django.urls import path
from accounts.views import check_email, get_banks, verify_bank_account
from products.views import get_subcategories

urlpatterns = [
    path("check-email/", check_email, name="check_email"),
    path("get-banks/", get_banks, name="get-banks"),
    path("verify-bank-account/", verify_bank_account, name="verify-bank-account"),
    path('get-subcategories/<int:category_id>/', get_subcategories, name='get-subcategories'),
]
