from django.contrib.auth import login
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from email_validator import validate_email

from accounts.models import User, VendorProfile, VendorStatus, UserTypes
from accounts.services.user_service import UserService
from services.util import CustomRequestUtil, compare_password


class VendorService(CustomRequestUtil):
    def create_single(self, payload):

        user = self.auth_user

        # business
        business_name = payload.get("business_name")
        store_name = payload.get("store_name")
        bank_name = payload.get("bank_name")
        account_number = payload.get("account_number")
        id_card = payload.get("id_card")
        profile_photo = payload.get("profile_photo")
        business_logo = payload.get("business_logo")
        business_email = payload.get("business_email")
        business_address = payload.get("business_address")
        business_phone = payload.get("business_phone")

        try:
            business_email_info = validate_email(business_email, check_deliverability=True)
            business_email = business_email_info.normalized
        except Exception as e:
            return None, self.make_error("Please enter a valid business email address")


        # personal
        if not self.auth_user:
            first_name = payload.get("first_name")
            last_name = payload.get("last_name")
            phone = payload.get("phone")
            email = payload.get("email")
            address = payload.get("address")
            password = payload.get("password")


            try:
                email_info = validate_email(email, check_deliverability=True)
                email = email_info.normalized
            except Exception as e:
                return None, self.make_error("Please enter a valid email address")

            # user_service = UserService(self.request)
            # existing_user, _ = user_service.find_user_by_email(email)
            # if existing_user:
            #     return None, self.make_error("User with email already exist")

            user, is_created = User.available_objects.get_or_create(
                email=email,
                defaults=dict(
                    last_name=last_name,
                    first_name=first_name,
                    phone_number=phone,
                    address=address,
                    password=make_password(password)
                )
            )


        vp, is_vp_created = VendorProfile.available_objects.get_or_create(
            user=user,
            defaults=dict(
                business_name=business_name,
                store_name=store_name,
                bank_name=bank_name,
                account_number=account_number,
                business_email=business_email,
                business_phone=business_phone,
                business_address=business_address
            )
        )

        if not is_vp_created:

            return None, self.make_error("Vendor profile already exists for this user")

        vp.status = VendorStatus.pending
        vp.id_card = id_card
        vp.profile_photo = profile_photo
        vp.business_logo = business_logo
        vp.save(save_files=True)

        user.user_type = UserTypes.vendor
        user.save()

        message = "Vendor application request has been submitted successfully. An email will be sent to you with an update"

        # TODO: send email

        return message, None


    def find_vendor_by_email(self, email):
        vendor = VendorProfile.objects.filter(
            Q(user__email__iexact=email) | Q(business_email__iexact=email)
        ).first()
        if not vendor:
            return None, self.make_error(f"Vendor with email '{email}' not found")

        return vendor, None

    def update_single(self, payload):
        vendor_profile = self.auth_vendor_profile

        if not vendor_profile:
            return None, self.make_error("Access denied, vendor profile not found.")

        user = self.auth_user

        user.first_name = payload.get('first_name', user.first_name)
        user.last_name = payload.get('last_name', user.last_name)
        user.address = payload.get('address', user.address)
        user.phone_number = payload.get('phone', user.phone_number)
        user.save()

        vendor_profile.business_name = payload.get('business_name', vendor_profile.business_name)
        vendor_profile.store_name = payload.get('store_name', vendor_profile.store_name)
        vendor_profile.bank_name = payload.get('bank_name', vendor_profile.bank_name)
        vendor_profile.account_number = payload.get('account_number', vendor_profile.account_number)
        vendor_profile.business_email = payload.get('business_email', vendor_profile.business_email)
        vendor_profile.business_address = payload.get('business_address', vendor_profile.business_address)

        if payload.get('business_logo'):
            vendor_profile.business_logo = payload.get('business_logo')
        if payload.get('id_card'):
            vendor_profile.id_card = payload.get('id_card')
        if payload.get('profile_photo'):
            vendor_profile.profile_photo = payload.get('profile_photo')

        if payload.get('business_logo') or payload.get('id_card') or payload.get('profile_photo'):
            vendor_profile.save(save_files=True)
        else:
            vendor_profile.save()

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

        message = "Your vendor profile was updated"

        return message, None


