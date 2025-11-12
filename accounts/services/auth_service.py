import os
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.utils import timezone

from accounts.models import OTPRequest, OTPTypes
from accounts.services.user_service import UserService
from services.util import CustomRequestUtil, compare_password, generate_otp
from crm.tasks import send_email_notification


class AuthService(CustomRequestUtil):
    def login(self, payload):
        email = payload.get("email")
        password = payload.get("password")

        user = authenticate(self.request, email=email, password=password)

        if not user:
            return None, self.make_error("Email/Password is not correct!")

        if not user.is_verified:

            self.create_otp_request(
                otp_type=OTPTypes.signup, email=email
            )

            self.request.session["email"] = email
            self.request.session["otp_type"] = OTPTypes.signup

            return "verify-otp", "You are yet to verify your email. Please check your registered email for an OTP."

        login(self.request, user)

        message = "Login successful"

        return message, None

    def signup(self, payload):

        user, error = UserService(self.request).create_single(payload)
        if error:
            return None, error

        send_email_notification.delay("emails/welcome.html", f"Welcome to {os.getenv('APP_NAME')}", user.email, )

        message = "Your signup was successful"

        return message, None

    def logout(self):

        logout(self.request)
        message = "Logout successful"

        return message, None

    def forgot_password(self, payload):
        email = payload.get("email")

        user, error = UserService(self.request).find_user_by_email(email)
        if error:
            return None, error

        self.create_otp_request(user=user, otp_type=OTPTypes.password_reset)

        message = "An OTP has been sent to your email."

        return message, None


    def verify_otp(self, payload):
        email = payload.get("email")
        otp = payload.get("otp")
        otp_type = payload.get("otp_type")

        user, error = UserService(self.request).find_user_by_email(email)
        if error:
            return None, error

        otp_request = self.get_otp_request(email, otp_type)

        if not otp_request:
            return None, "No OTP request found"

        if otp_request.is_used :
            return None, "OTP has already been used"

        if otp_request.is_expired:
            return None, "OTP has expired"

        if not compare_password(otp, otp_request.otp):
            return None, "OTP is not valid"

        otp_request.is_used = True
        otp_request.save(update_fields=["is_used"])

        if otp_type == OTPTypes.signup:
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            login(self.request, user)

        return "Verification successful", None



    def create_new_password(self, payload):
        email = payload.get("email")
        new_password = payload.get("new_password")
        confirm_password = payload.get("confirm_password")

        if new_password != confirm_password:
            return None, self.make_error("Password mismatch")

        user, error = UserService(self.request).find_user_by_email(email)
        if error:
            return None, error

        user.set_password(new_password)
        user.save()

        message = "Your password has been reset successfully"

        self.request.session.pop('email', None)
        self.request.session.pop('otp_type', None)


        return message, None

    def get_otp_request(self, email, otp_type):
        return OTPRequest.objects.filter(user__email=email, otp_type=otp_type).last()

    def create_otp_request(self, user=None, otp_type=None, email=None):
        otp, hashed_otp = generate_otp()

        if not user and email:
            user, error = UserService(self.request).find_user_by_email(email)
            if error:
                return None, error

        otp_request = OTPRequest.objects.create(
            user=user, otp_type=otp_type,
            otp=hashed_otp, expires_at=timezone.now() + timedelta(minutes=15)
        )

        OTPRequest.objects.filter(user=user, is_used=False).exclude(pk=otp_request.pk).update(
            expires_at=timezone.now()
        )
        email_context = {
            'otp_code' : otp,
            'first_name' : user.first_name
        }

        if otp_type == OTPTypes.signup:
            email_template = 'welcome.html'
            subject = f"Welcome to {os.getenv('APP_NAME')}"
        elif otp_type == OTPTypes.login:
            email_template = None
            subject = None
        else:
            email_template = 'forgot-password.html'
            subject = 'Forgot Password'

        send_email_notification.delay(f'emails/{email_template}', subject, user.email, email_context)

        return otp

    def has_exceeded_otp_limit(self, user, limit=3, minutes=10):
        """
        Returns True if the user has requested OTP more than `limit`
        times within the past `minutes`.
        """
        from django.utils import timezone
        from datetime import timedelta

        time_threshold = timezone.now() - timedelta(minutes=minutes)
        recent_requests = OTPRequest.objects.filter(
            user=user,
            created_at__gte=time_threshold
        ).count()

        return recent_requests >= limit


