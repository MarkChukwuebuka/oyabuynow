from django.urls import path
from accounts.views import check_email

urlpatterns = [
    path("check-email/", check_email, name="check_email"),
]
