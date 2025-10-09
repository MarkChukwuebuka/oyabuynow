from django.contrib.auth import login
from django.contrib.auth.hashers import make_password
from email_validator import validate_email

from accounts.models import User, VendorProfile
from services.util import CustomRequestUtil, compare_password


class UserService(CustomRequestUtil):
    def create_single(self, payload):
        """Payload requirements:
        {
        email: String,
        password: String,
        first_name: String,
        last_name: String
        }
        """

        email = payload.get("email")
        password = payload.get("password")
        first_name = payload.get("first_name")
        last_name = payload.get("last_name")
        phone = payload.get("phone")
        address = payload.get("address")

        try:
            email_info = validate_email(email, check_deliverability=True)
            email = email_info.normalized
        except Exception as e:
            return None, self.make_error("Please enter a valid email address")

        existing_user, _ = self.find_user_by_email(email)
        if existing_user:
            return None, self.make_error("User with email already exist")

        user, is_created = User.available_objects.get_or_create(
            email=email,
            defaults=dict(
                last_name=last_name,
                first_name=first_name,
                phone=phone,
                address=address,
                password=make_password(password)
            )
        )

        if not is_created:
            return None, self.make_error("User already exist")

        return user, None

    def find_user_by_email(self, email):
        user = User.objects.filter(email__iexact=email).first()
        vendor = VendorProfile.objects.filter()
        if not user:
            return None, self.make_error(f"User with email '{email}' not found")

        return user, None

    def update_single(self, payload):
        user = self.auth_user
        user.first_name = payload.get('first_name', user.first_name)
        user.last_name = payload.get('last_name', user.last_name)
        user.phone_number = payload.get('phone', user.phone_number)
        user.save()

        current_password = payload.get('current_password')
        new_password = payload.get('new_password')
        confirm_password = payload.get('confirm_password')

        if current_password and new_password:

            if new_password != confirm_password:
                return None, self.make_error("Password Mismatch")

            if not compare_password(current_password, user.password):
                return None, self.make_error("Access denied, invalid password.")

            user.set_password(payload.get("new_password"))
            user.save()

            login(self.request, user)

        message = "Your profile was updated"

        return message, None


