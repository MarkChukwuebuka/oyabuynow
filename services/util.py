import random
import string
from typing import Union, TypeVar

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from django.contrib import messages
import phonenumbers
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.timezone import is_aware, make_aware

T = TypeVar("T")


def generate_code(length):
    characters = string.ascii_letters + string.digits
    code = ''.join(random.choice(characters) for _ in range(length))
    return code


class CustomPermissionRequired(PermissionRequiredMixin):
    def has_permission(self) -> bool:
        perms = self.get_permission_required()
        user = self.request.user

        if user.is_anonymous:
            return False

        if user.is_staff:
            return user.is_superuser or user.has_permission(perms)

        client = user.get_active_client()

        return client.has_permission(perms)


class CustomRequestUtil(CustomPermissionRequired):
    context: dict = None
    context_object_name = None
    template_name = None
    template_on_error = None
    extra_context_data: dict = None
    page_size = 100

    def __init__(self, request):
        self.request = request
        self.permission_required = None


    @property
    def auth_user(self):
        user = self.request.user if self.request and self.request.user else None
        if isinstance(user, AnonymousUser):
            user = None

        return user

    @property
    def auth_vendor_profile(self):
        if self.auth_user:
            return self.auth_user.vendor_profile
        else:
            return None

    def log_activity(self, activity, data, note=None):
        from crm.services.activity_log import ActivityLogService

        if not note:
            note = f"{self.auth_user} {str(activity)} with records related to {data}"

        activity_log_service = ActivityLogService(self.request)
        activity_log_service.create(activity, note)

        print(self.auth_user, activity, note)

    def log_error(self, error):
        print(error)

    def make_error(self, message=None, error=None):
        if error:
            self.log_error(error)
        return message

    def process_request(self, request, target_view=None, target_function=None, **extra_args):

        if not self.context:
            self.context = dict()


        self.context['request'] = request


        if self.permission_required:
            if not self.has_permission():
                response_raw_data = (None, "You do not have permission to perform this action.")
                return self.__handle_request_response(response_raw_data, target_view)

        if self.extra_context_data:
            for key, val in self.extra_context_data.items():
                self.context[key] = val

        response_raw_data = None

        if target_function:
            response_raw_data: Union[tuple, T] = target_function(**extra_args)

        return self.__handle_request_response(response_raw_data, target_view)

    def __handle_request_response(self, response_raw_data, target_view):
        response, error_detail = None, None

        if isinstance(response_raw_data, tuple):
            response, error_detail = response_raw_data
        else:
            response = response_raw_data

        if error_detail:
            messages.error(self.request, error_detail)
            if self.template_on_error:

                return render(self.request, self.template_on_error, self.context)
        else:
            if isinstance(response, str):
                messages.success(self.request, response)
            else:
                self.context[self.context_object_name] = response

        if self.template_name:
            return render(self.request, self.template_name, self.context)

        if target_view:
            return redirect(target_view)

        return redirect('/')



def format_phone_number(phone_number, region_code=None):
    if not region_code:
        region_code = "NG"
    try:
        x = phonenumbers.parse(phone_number, region_code)
        phone_number = phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.E164)

        if phonenumbers.is_valid_number_for_region(x, region_code):
            return phone_number
    except:
        pass

    return None


def compare_password(input_password, hashed_password):
    return check_password(input_password, hashed_password)


def send_email(html_template, context, subject, email):
    html_message = render_to_string(html_template, context=context)
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    message = EmailMessage(subject, html_message, email_from, recipient_list)
    message.content_subtype = 'html'
    message.send()

    return None


def generate_otp():
    if settings.DEBUG:
        otp = "123456"
    else:
        otp = str(random.randint(1, 999999)).zfill(6)

    hashed_otp = make_password(otp)

    return otp, hashed_otp


def check_otp_time_expired(expires_at):
    if expires_at is None:
        return True
    if not is_aware(expires_at):
        expires_at = make_aware(expires_at)

    current_time = timezone.now()

    return current_time > expires_at


def compare_password(input_password, hashed_password):
    return check_password(input_password, hashed_password)
