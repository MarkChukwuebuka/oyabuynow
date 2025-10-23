import json

import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum, F
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User, VendorStatus
from accounts.services.auth_service import AuthService
from accounts.services.user_service import UserService
from accounts.services.vendor_service import VendorService
from payments.models import Order, OrderItem, OrderStatusChoices, PaymentStatus
from payments.services.order_service import OrderService, OrderItemService
from products.models import Product
from products.services.product_service import ProductService
from products.services.wishlist_service import WishlistService
from services.util import CustomRequestUtil, vendor_required, customer_required


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
    template_on_error = "frontend/forgot-password.html"

    def get(self, request, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        auth_service = AuthService(self.request)
        self.template_name = None
        self.template_on_error = 'frontend/forgot-password.html'

        payload = {
            'email': request.POST.get('email')
        }

        request.session["email"] = request.POST.get("email")

        return self.process_request(
            request, target_view="verify-otp", target_function=auth_service.forgot_password, payload=payload
        )


class VerifyOtpView(View, CustomRequestUtil):
    template_name = 'frontend/verify-otp.html'
    extra_context_data = {
        "title": "Verify OTP",
    }
    template_on_error = "frontend/verify-otp.html"

    def get(self, request, *args, **kwargs):
        self.extra_context_data["email"] = request.session.get("email")
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        auth_service = AuthService(self.request)
        self.template_name = None
        self.template_on_error = 'frontend/verify-otp.html'

        payload = {
            'otp': request.POST.get('otp'),
            'email': request.POST.get('email'),
        }

        return self.process_request(
            request, target_view="create-new-password", target_function=auth_service.verify_otp, payload=payload
        )

class CreateNewPasswordView(View, CustomRequestUtil):
    template_name = 'frontend/create-new-password.html'
    extra_context_data = {
        "title": "Create New Password",
    }
    template_on_error = "frontend/create-new-password.html"

    def get(self, request, *args, **kwargs):

        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        auth_service = AuthService(self.request)
        self.template_name = None
        self.template_on_error = 'frontend/create-new-password.html'

        payload = {
            'new_password': request.POST.get('new_password'),
            'confirm_password': request.POST.get('confirm_password'),
            'email': request.session.get("email"),
        }

        return self.process_request(
            request, target_view="login", target_function=auth_service.create_new_password, payload=payload
        )


class UserDashboardView(LoginRequiredMixin, View, CustomRequestUtil):
    template_name = 'backend/user-dashboard.html'

    extra_context_data = {
        "title": "Dashboard",
    }

    @customer_required
    def get(self, request, *args, **kwargs):
        completed_orders = Order.objects.filter(user=self.auth_user, payment_status=PaymentStatus.paid).count() or 0
        pending_orders = Order.objects.filter(user=self.auth_user, payment_status=PaymentStatus.processing).count() or 0
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
    template_name = 'frontend/vendor-dashboard-home.html'
    context_object_name = 'vendor'

    extra_context_data = {
        "title": "Dashboard",
    }

    @vendor_required
    def get(self, request, *args, **kwargs):
        vendor_service = VendorService(self.request)
        order_service = OrderItemService(request)
        product_service = ProductService(request)

        if self.auth_vendor_profile.status == VendorStatus.pending:
            messages.info(request, "Your Vendor application is being processed")
            return redirect("home")

        if self.auth_vendor_profile.status == VendorStatus.rejected:
            messages.error(
                request,
                f"Your Vendor application was rejected. {self.auth_vendor_profile.reason_for_rejection}, please try applying again."
            )
            return redirect("onboard-vendor")

        total_orders = Order.objects.filter(items__product__created_by=self.auth_user).distinct().count()
        delivered_orders = OrderItem.objects.filter(
            product__created_by=self.auth_user, status=OrderStatusChoices.delivered, order__payment_status=PaymentStatus.paid
        ).count() or 0
        shipped_orders = OrderItem.objects.filter(
            product__created_by=self.auth_user, status=OrderStatusChoices.shipped, order__payment_status=PaymentStatus.paid
        ).count() or 0
        pending_orders = OrderItem.objects.filter(
            product__created_by=self.auth_user, status=OrderStatusChoices.ordered, order__payment_status=PaymentStatus.paid
        ).count() or 0

        total_products = Product.available_objects.filter(created_by=self.auth_user).count() or 0

        total_sales = OrderItem.objects.filter(
            product__created_by=self.auth_user, order__payment_status=PaymentStatus.paid
        ).aggregate(
            total=Sum("price")
        )["total"] or 0

        latest_order_items = order_service.fetch_list()[:5]
        trending_products = product_service.fetch_list(vendor=self.auth_vendor_profile).order_by('-views')[:5]

        self.extra_context_data["shipped_orders"] = shipped_orders
        self.extra_context_data["delivered_orders"] = delivered_orders
        self.extra_context_data["trending_products"] = trending_products
        self.extra_context_data["total_orders"] = total_orders
        self.extra_context_data["pending_orders"] = pending_orders
        self.extra_context_data["latest_order_items"] = latest_order_items
        self.extra_context_data["total_sales"] = total_sales
        self.extra_context_data["total_products"] = total_products

        return self.process_request(request, target_function=vendor_service.fetch_authenticated_vendor)






class VendorProductListView(LoginRequiredMixin, View, CustomRequestUtil):
    template_name = 'frontend/vendor-dashboard-products.html'
    context_object_name = 'vendor'

    extra_context_data = {
        "title": "Products",
    }

    @vendor_required
    def get(self, request, *args, **kwargs):

        if self.auth_vendor_profile.status == VendorStatus.pending:
            messages.info(request, "Your Vendor application is being processed")
            return redirect("home")

        if self.auth_vendor_profile.status == VendorStatus.rejected:
            messages.error(
                request,
                f"Your Vendor application was rejected. {self.auth_vendor_profile.reason_for_rejection}, please try applying again."
            )
            return redirect("onboard-vendor")

        vendor_service = VendorService(self.request)
        product_service = ProductService(request)

        vendor_products = product_service.fetch_list(vendor=self.auth_vendor_profile, paginate=True)

        self.extra_context_data["vendor_products"] = vendor_products


        return self.process_request(request, target_function=vendor_service.fetch_authenticated_vendor)



class VendorOrdersView(LoginRequiredMixin, View, CustomRequestUtil):
    template_name = 'frontend/vendor-dashboard-orders.html'
    context_object_name = 'vendor'

    extra_context_data = {
        "title": "My Orders",
    }

    @vendor_required
    def get(self, request, *args, **kwargs):
        if self.auth_vendor_profile.status == VendorStatus.pending:
            messages.info(request, "Your Vendor application is being processed")
            return redirect("home")

        if self.auth_vendor_profile.status == VendorStatus.rejected:
            messages.error(
                request,
                f"Your Vendor application was rejected. {self.auth_vendor_profile.reason_for_rejection}, please try applying again."
            )
            return redirect("onboard-vendor")

        vendor_service = VendorService(self.request)
        order_service = OrderItemService(request)

        order_items = order_service.fetch_list(paginate=True)

        self.extra_context_data["order_items"] = order_items

        return self.process_request(request, target_function=vendor_service.fetch_authenticated_vendor)



class VendorProfileView(LoginRequiredMixin, View, CustomRequestUtil):
    template_name = 'frontend/vendor-dashboard-profile.html'
    context_object_name = 'vendor'

    extra_context_data = {
        "title": "Vendor Profile",
    }

    @vendor_required
    def get(self, request, *args, **kwargs):

        vendor_service = VendorService(self.request)

        if self.auth_vendor_profile.status == VendorStatus.rejected:
            messages.error(
                request,
                f"Your Vendor application was rejected. {self.auth_vendor_profile.reason_for_rejection}, please try applying again."
            )
            return redirect("onboard-vendor")


        return self.process_request(request, target_function=vendor_service.fetch_authenticated_vendor)


    def post(self, request, *args, **kwargs):
        self.template_name = None
        self.template_on_error = 'frontend/vendor-dashboard-profile.html'
        vendor_service = VendorService(self.request)

        payload = {
            'bank_name': request.POST.get('bank_name'),
            'account_number': request.POST.get('account_number'),
            'business_phone': request.POST.get('business_phone'),
            'store_name': request.POST.get('store_name'),
            'business_email': request.POST.get('business_email'),
            'business_logo': request.FILES.get('business_logo'),
        }

        return self.process_request(
            request, target_view="vendor-dashboard-profile", target_function=vendor_service.update_single, payload=payload
        )







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

class OnboardVendorView(View, CustomRequestUtil):
    template_name = 'frontend/onboard-vendor.html'
    extra_context_data = {
        "title": "Become a Vendor",
    }

    def get(self, request, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        vendor_service = VendorService(self.request)
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
            request, target_view="home", target_function=vendor_service.create_single, payload=payload
        )



class UserLogoutView(View, CustomRequestUtil):

    def get(self, request, *args, **kwargs):
        auth_service = AuthService(self.request)

        return self.process_request(
            request, target_function=auth_service.logout, target_view="home"
        )



@csrf_exempt  # optional if you're not using CSRF tokens from JS
def resend_otp(request):

    if request.method != "POST":
        return JsonResponse({"error": "Only POST method is allowed"}, status=405)

    try:
        user_service = UserService(request)
        auth_service = AuthService(request)

        body = json.loads(request.body)
        email = body.get("email")

        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)

        user, error = user_service.find_user_by_email(email)
        if not user:
            return JsonResponse(
                {"error": f"{error}"}, status=404
            )

        if auth_service.has_exceeded_otp_limit(user):
            return JsonResponse(
                {"error": "Too many OTP requests. Try again later."},
                status=429
            )

        auth_service.create_password_reset_request(user)

        return JsonResponse({
            "success": True,
            "message": f"OTP has been resent to your email"
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



def check_email(request):
    email = request.GET.get("email", "").strip().lower()
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({"exists": exists})



def verify_bank_account(request):
    account_number = request.GET.get("account_number")
    bank_code = request.GET.get("bank_code")

    if not account_number or not bank_code:
        return JsonResponse({"status": False, "message": "Missing parameters"}, status=400)

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