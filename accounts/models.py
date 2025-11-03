from datetime import timedelta

import cloudinary
from cloudinary.models import CloudinaryField
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import TextChoices
from django.utils import timezone


from crm.models import BaseModel


class VendorStatus(models.TextChoices):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"

class UserTypes(TextChoices):
    admin = "Admin"
    vendor = "Vendor"
    customer = "Customer"

class OTPTypes(TextChoices):
    login = "Login"
    signup = "Signup"
    password_reset = "Password Reset"


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password"""
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('user_type', UserTypes.admin)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """Custom user model that uses email instead of username"""

    email = models.EmailField(
        unique=True,
        max_length=254,
        help_text='Required. 254 characters or fewer. Must be a valid email address.'
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    user_type = models.CharField(max_length=150, default=UserTypes.customer, choices=UserTypes.choices)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.'
    )

    is_verified = models.BooleanField(
        default=False,
        help_text='Designates whether this user has confirmed his/her email.'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into this admin site.'
    )
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already required as USERNAME_FIELD

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between"""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email

    def get_short_name(self):
        """Return the short name for the user"""
        return self.first_name or self.email


class OTPRequest(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=False,
        related_name="otp_requests"
    )
    otp = models.CharField(max_length=255, default="123456")
    otp_type = models.CharField(max_length=25, choices=OTPTypes.choices, default=OTPTypes.signup)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True)

    @property
    def is_expired(self):
        """Check if the OTP has expired"""
        return timezone.now() > self.expires_at

    @classmethod
    def cleanup_expired(cls):
        """Delete all expired or very old OTPs"""
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
        cls.objects.filter(created_at__lt=timezone.now() - timedelta(days=7)).delete()


class VendorProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    business_name = models.CharField(max_length=255, null=True, blank=True)
    business_phone = models.CharField(max_length=255, null=True, blank=True)
    store_name = models.CharField(max_length=255, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=255, null=True, blank=True)
    business_address = models.TextField(blank=True, null=True)
    business_logo = CloudinaryField('business_logo', blank=True, null=True)
    rating = models.PositiveIntegerField(null=True, blank=True)
    id_card = CloudinaryField('id_card', blank=True, null=True)
    profile_photo = CloudinaryField('profile_photo', blank=True, null=True)
    reason_for_rejection = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=VendorStatus.choices, default=VendorStatus.pending
    )
    business_email = models.EmailField(max_length=254, blank=True, null=True)

    def __str__(self):
        return f"{self.business_name} - {self.user.email}"

    def save(self, *args, **kwargs):
        save_files = kwargs.pop("save_files", False)
        upload_fields = ["business_logo", "id_card", "profile_photo"]

        if save_files:
            if self.pk:  # updating
                old = type(self).objects.filter(pk=self.pk).first()
            else:
                old = None

            for field in upload_fields:
                file_field = getattr(self, field)
                old_value = getattr(old, field) if old else None

                if file_field and (not old_value or str(file_field) != str(old_value)):
                    upload = cloudinary.uploader.upload(
                        file_field,
                        folder=field,
                        public_id=self.business_name.replace(" ", "_").lower(),
                        overwrite=True,
                        resource_type="image"
                    )
                    setattr(self, field, upload["public_id"])

        if self.pk:
            from services.util import send_email

            email = self.business_email if self.business_email else self.user.email
            email_context = {
                'vendor_name' : self.business_name
            }
            old_vendor = VendorProfile.objects.get(pk=self.pk)
            if old_vendor.status != self.status and self.status == VendorStatus.approved:
                self.user.user_type = UserTypes.vendor
                self.user.save()

                send_email(
                    'emails/vendor-application-approved.html', 'Vendor Application was Approved',
                    email, email_context
                )


            if old_vendor.status != self.status and self.status == VendorStatus.rejected:

                self.user.save()

                email_context['decline_reason'] = self.reason_for_rejection

                send_email(
                    'emails/vendor-application-rejected.html', 'Vendor Application was Declined',
                    email, email_context
                )


        super().save(*args, **kwargs)

