from django.views import View

from products.services.product_service import ProductService
from services.util import CustomRequestUtil


# Create your views here.
class HomeView(View, CustomRequestUtil):
    template_name = "frontend/index.html"
    extra_context_data = {
        "title": "Welcome",
    }

    def get(self, request, *args, **kwargs):
        product_service = ProductService(self.request)

        top_rated = product_service.fetch_list()[:10]
        new_arrivals = product_service.fetch_list()[:10]
        best_seller = product_service.fetch_list()[:10]

        self.extra_context_data["top_rated"] = top_rated
        self.extra_context_data["new_arrivals"] = new_arrivals
        self.extra_context_data["best_seller"] = best_seller

        return self.process_request(request)


class ContactView(View, CustomRequestUtil):
    template_name = "frontend/contact-us.html"
    extra_context_data = {
        "title": "Contact Us",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)


class FAQView(View, CustomRequestUtil):
    template_name = "faqs.html"
    extra_context_data = {
        "title": "FAQS",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)


class AboutView(View, CustomRequestUtil):
    template_name = "about.html"
    extra_context_data = {
        "title": "About Us",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)
