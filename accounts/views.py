import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.views import View

from accounts.models import User
from accounts.services.auth_service import AuthService
from accounts.services.user_service import UserService
from payments.models import Order, Payment
from payments.services.order_service import OrderService
from products.services.wishlist_service import WishlistService
from services.util import CustomRequestUtil


class UserLoginView(View, CustomRequestUtil):
    template_name = 'frontend/login.html'
    extra_context_data = {
        "title": "Sign In",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        auth_service = AuthService(self.request)

        self.template_name = None
        self.template_on_error = 'frontend/login.html'

        payload = {
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
        }

        next_url = request.POST.get('next', request.GET.get('next', '/'))

        return self.process_request(
            request, target_view=next_url, target_function=auth_service.login, payload=payload
        )


class UserSignupView(View, CustomRequestUtil):
    template_name = 'frontend/signup.html'
    extra_context_data = {
        "title": "Sign Up",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        auth_service = AuthService(self.request)
        self.template_name = None
        self.template_on_error = 'frontend/signup.html'

        payload = {
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'first_name': request.POST.get('firstName'),
            'last_name': request.POST.get('lastName'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address'),
        }

        return self.process_request(
            request, target_view="login", target_function=auth_service.signup, payload=payload
        )



class UserForgotPasswordView(View, CustomRequestUtil):
    template_name = 'frontend/forgot-password.html'
    extra_context_data = {
        "title": "Forgot Password",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        auth_service = AuthService(self.request)
        self.template_name = None
        self.template_on_error = 'frontend/forgot-password.html'

        payload = {
            'email': request.POST.get('email')
        }

        return self.process_request(
            request, target_view="login", target_function=auth_service.signup, payload=payload
        )


class UserDashboardView(LoginRequiredMixin, View, CustomRequestUtil):
    template_name = 'backend/user-dashboard.html'

    extra_context_data = {
        "title": "Dashboard",

    }

    def get(self, request, *args, **kwargs):
        completed_orders = Payment.objects.filter(user=self.auth_user, verified=True).count() or 0
        pending_orders = Order.objects.filter(user=self.auth_user, paid=False).count() or 0
        orders_count = Order.objects.filter(user=self.auth_user).count() or 0
        total_spent = Order.objects.filter(user=self.auth_user, refunded=False).aggregate(
            total_spent=Sum("total_cost")
        )["total_spent"] or 0
        wishlist_products = WishlistService(request).fetch_list()
        orders = OrderService(request).fetch_list()

        self.extra_context_data["completed_orders"] = completed_orders
        self.extra_context_data["orders_count"] = orders_count
        self.extra_context_data["pending_orders"] = pending_orders
        self.extra_context_data["total_spent"] = total_spent
        self.extra_context_data["orders"] = orders

        return self.process_request(request)



class VendorDashboardView(LoginRequiredMixin, View, CustomRequestUtil):
    template_name = 'backend/vendor-dashboard.html'

    extra_context_data = {
        "title": "Dashboard",

    }

    def get(self, request, *args, **kwargs):
        completed_orders = Payment.objects.filter(user=self.auth_user, verified=True).count() or 0
        pending_orders = Order.objects.filter(user=self.auth_user, paid=False).count() or 0
        orders_count = Order.objects.filter(user=self.auth_user).count() or 0
        total_spent = Order.objects.filter(user=self.auth_user, refunded=False).aggregate(
            total_spent=Sum("total_cost")
        )["total_spent"] or 0
        wishlist_products = WishlistService(request).fetch_list()
        orders = OrderService(request).fetch_list()

        self.extra_context_data["completed_orders"] = completed_orders
        self.extra_context_data["orders_count"] = orders_count
        self.extra_context_data["pending_orders"] = pending_orders
        self.extra_context_data["total_spent"] = total_spent
        self.extra_context_data["orders"] = orders

        return self.process_request(request)




class UpdateUserView(LoginRequiredMixin, View, CustomRequestUtil):
    template_name = 'backend/settings.html'
    extra_context_data = {
        "title": "Settings",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        user_service = UserService(self.request)
        self.template_name = None
        self.template_on_error = 'backend/settings.html'

        payload = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'phone': request.POST.get('phone'),
            'current_password': request.POST.get('current_password'),
            'new_password': request.POST.get('new_password'),
            'confirm_password': request.POST.get('confirm_password')
        }

        return self.process_request(
            request, target_view="dashboard", target_function=user_service.update_single, payload=payload
        )

class OnboardVendorView(LoginRequiredMixin, View, CustomRequestUtil):
    template_name = 'frontend/onboard-vendor.html'
    extra_context_data = {
        "title": "Become a Vendor",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        user_service = UserService(self.request)
        self.template_name = None
        self.template_on_error = 'frontend/onboard-vendor.html'

        payload = {
            'bank_name': request.POST.get('bank_name'),
            'account_number': request.POST.get('account_number'),
            'business_email': request.POST.get('business_email'),
            'business_name': request.POST.get('business_name'),
            'store_name': request.POST.get('store_name'),
            'business_phone': request.POST.get('business_phone'),
            'business_address': request.POST.get('business_address'),
            'business_logo': request.FILES.get('business_logo'),
            'id_card': request.FILES.get('id_card'),
            'profile_photo': request.FILES.get('profile_photo')
        }

        if not self.auth_user:
            payload['email'] = request.POST.get('email')
            payload['first_name'] = request.POST.get('first_name')
            payload['last_name'] = request.POST.get('last_name')
            payload['phone'] = request.POST.get('phone')
            payload['password'] = request.POST.get('password')

        return self.process_request(
            request, target_view="home", target_function=user_service.update_single, payload=payload
        )



class UserLogoutView(View, CustomRequestUtil):

    def get(self, request, *args, **kwargs):
        auth_service = AuthService(self.request)

        return self.process_request(
            request, target_function=auth_service.logout, target_view="home"
        )




def check_email(request):
    email = request.GET.get("email", "").strip().lower()
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({"exists": exists})



def verify_bank_account(request):
    account_number = request.GET.get("account_number")
    bank_code = request.GET.get("bank_code")

    if not account_number or not bank_code:
        return JsonResponse({"status": False, "message": "Missing parameters"}, status=400)

    print(account_number)

    url = f"https://api.paystack.co/bank/resolve?account_number={account_number}&bank_code={bank_code}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if response.status_code == 200 and data.get("status"):
        return JsonResponse({
            "status": True,
            "account_name": data["data"]["account_name"]
        })
    else:
        return JsonResponse({
            "status": False,
            "message": data.get("message", "Verification failed")
        })




def get_banks(request):
    url = "https://api.paystack.co/bank"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
    }
    response = requests.get(url, headers=headers)
    data = response.json()

    if response.status_code == 200 and data.get("status"):
        banks = [
            {"name": bank["name"], "code": bank["code"]}
            for bank in data["data"]
        ]
        return JsonResponse({"status": True, "banks": banks})
    else:
        return JsonResponse({
            "status": False,
            "message": "Could not load banks"
        })