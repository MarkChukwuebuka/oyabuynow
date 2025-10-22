from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.utils import timezone

from accounts.models import PasswordResetRequest
from accounts.services.user_service import UserService
from services.util import CustomRequestUtil, compare_password, check_otp_time_expired, generate_otp


class AuthService(CustomRequestUtil):
    def login(self, payload):
        email = payload.get("email")
        password = payload.get("password")

        user = authenticate(self.request, email=email, password=password)


        if not user:
            return None, self.make_error("Email/Password is not correct!")

        login(self.request, user)

        message = "Login successful"

        return message, None

    def signup(self, payload):

        user, error = UserService(self.request).create_single(payload)
        if error:
            return None, error

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

        self.create_password_reset_request(user)

        message = "If an account with that email exists, a password reset link has been sent."

        return message, None

    def verify_otp(self, payload):
        email = payload.get("email")
        otp = payload.get("otp")

        user, error = UserService(self.request).find_user_by_email(email)
        if error:
            return None, error

        password_reset_request = self.get_password_request(user)

        if password_reset_request:
            if not compare_password(otp, password_reset_request.otp):
                return None, "OTP is not valid"

            if password_reset_request.is_used or password_reset_request.is_expired:
                return None, "OTP has expired"

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

        return message, None

    def get_password_request(self, email):
        return PasswordResetRequest.objects.filter(user__email=email).order_by("-created_at").first()

    def create_password_reset_request(self, user):
        otp, hashed_otp = generate_otp()
        reset_request = PasswordResetRequest.objects.create(
            user=user, is_used=False,
            otp=hashed_otp, expires_at=timezone.now() + timedelta(minutes=30)
        )

        PasswordResetRequest.objects.filter(user=user, is_used=False).exclude(pk=reset_request.pk).update(
            expires_at=timezone.now()
        )

        # TODO: Implement email sending logic here.

        return otp

    def has_exceeded_otp_limit(self, user, limit=3, minutes=10):
        """
        Returns True if the user has requested OTP more than `limit`
        times within the past `minutes`.
        """
        from django.utils import timezone
        from datetime import timedelta

        time_threshold = timezone.now() - timedelta(minutes=minutes)
        recent_requests = PasswordResetRequest.objects.filter(
            user=user,
            created_at__gte=time_threshold
        ).count()

        return recent_requests >= limit


