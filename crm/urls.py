from django.urls import path

from crm.views import HomeView, ContactView, AboutView, PrivacyPolicyView, ReturnsAndRefundView, \
    TermsAndConditionsView

urlpatterns = [

    path('', HomeView.as_view(), name="home"),
    path('contact/', ContactView.as_view(), name="contact"),
    path('about/', AboutView.as_view(), name="about"),
    path('terms-and-conditions/', TermsAndConditionsView.as_view(), name="terms-and-conditions"),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name="privacy-policy"),
    path('returns-and-refund/', ReturnsAndRefundView.as_view(), name="returns-and-refund"),
]
