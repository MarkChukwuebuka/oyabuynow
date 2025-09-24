from django.contrib.auth.mixins import LoginRequiredMixin
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
    template_name = 'dashboard.html'

    extra_context_data = {
        "title": "Dashboard",

    }

    def get(self, request, *args, **kwargs):
        completed_orders = Payment.objects.filter(user=self.auth_user, verified=True).count() or 0
        pending_orders = Order.objects.filter(user=self.auth_user, paid=False).count() or 0
        orders_count = Order.objects.filter(user=self.auth_user).count() or 0
        wishlist_products = WishlistService(request).fetch_list()
        orders = OrderService(request).fetch_list()

        self.extra_context_data["completed_orders"] = completed_orders
        self.extra_context_data["orders_count"] = orders_count
        self.extra_context_data["pending_orders"] = pending_orders
        self.extra_context_data["wishlist_products"] = wishlist_products
        self.extra_context_data["orders"] = orders

        return self.process_request(request)




class UpdateUserView(LoginRequiredMixin, View, CustomRequestUtil):
    template_name = 'settings.html'
    extra_context_data = {
        "title": "Settings",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        user_service = UserService(self.request)
        self.template_name = None
        self.template_on_error = 'settings.html'

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