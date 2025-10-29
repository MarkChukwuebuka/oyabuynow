from django.urls import path

from crm.views import HomeView, ContactView, AboutView, FAQView
from products.views import SearchResultsView

urlpatterns = [

    path('', HomeView.as_view(), name="home"),
    path('contact/', ContactView.as_view(), name="contact"),
    path('faqs/', FAQView.as_view(), name="faqs"),
    path('about/', AboutView.as_view(), name="about"),
    path('search/', SearchResultsView.as_view(), name="search")
]
