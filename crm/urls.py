from django.urls import path

from crm.views import HomeView, ContactView, AboutView, FAQView

urlpatterns = [

    path('', HomeView.as_view(), name="home"),
    path('contact/', ContactView.as_view(), name="contact"),
    path('faqs/', FAQView.as_view(), name="faqs"),
    path('about/', AboutView.as_view(), name="about")
]
