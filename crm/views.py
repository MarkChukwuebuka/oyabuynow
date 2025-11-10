from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from crm.models import Banner, BannerTypeChoices
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

        self.request.session.pop('email', None)
        self.request.session.pop('otp_type', None)


        top_rated = product_service.fetch_list()[:10]
        new_arrivals = product_service.fetch_list()[:10]
        best_seller = product_service.fetch_list().order_by("-quantity_sold")[:10]
        trending_products = product_service.fetch_list().order_by("-views")[:5]
        products = product_service.get_random_products(12)
        banners = Banner.objects.filter(is_active=True).order_by("?")

        self.extra_context_data["top_rated"] = top_rated
        self.extra_context_data["banners"] = banners
        self.extra_context_data["new_arrivals"] = new_arrivals
        self.extra_context_data["best_seller"] = best_seller
        self.extra_context_data["trending_products"] = trending_products
        self.extra_context_data["products"] = products

        return self.process_request(request)



class ContactView(View, CustomRequestUtil):
    template_name = "frontend/contact-us.html"
    extra_context_data = {
        "title": "Contact Us",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)


class ReturnsAndRefundView(View, CustomRequestUtil):
    template_name = "frontend/returns-and-refunds.html"
    extra_context_data = {
        "title": "Returns And Refund Policy",
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



class PrivacyPolicyView(View, CustomRequestUtil):
    template_name = "frontend/privacy-policy.html"
    extra_context_data = {
        "title": "Privacy Policy",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)




class TermsAndConditionsView(View, CustomRequestUtil):
    template_name = "frontend/terms-and-conditions.html"
    extra_context_data = {
        "title": "Privacy Policy",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)


class BannerAPIView(View):
    def get(self, request):
        banner_type = request.GET.get('type', BannerTypeChoices.main)

        print(banner_type)
        if banner_type not in [BannerTypeChoices.main, BannerTypeChoices.side]:
            banner_type = BannerTypeChoices.main


        print(banner_type)
        banners = Banner.objects.filter(
            is_active=True,
            banner_type=banner_type
        ).order_by('order')

        data = [{
            'id': banner.id,
            'title': banner.title,
            'subtitle': banner.subtitle,
            'description': banner.description,
            'image': banner.image.url if banner.image else '',
            'discount_title': banner.discount_title,
            'discount_text': banner.discount_text,
            'banner_type': banner.banner_type,
            'order': banner.order
        } for banner in banners]

        return JsonResponse(data, safe=False)




def page_not_found(request, exception):
    return render(request, 'frontend/404.html', {'title':'Page Not Found'}, status=404)

def server_error(request):
    return render(request, 'frontend/500.html', {'title':'Server Error'}, status=404)


