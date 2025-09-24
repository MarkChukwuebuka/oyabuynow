import re

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.db.models import TextChoices, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


from crm.models import BaseModel


class UserTypes(TextChoices):
    admin = "Admin"
    vendor = "Vendor"
    customer = "Customer"


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
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.'
    )

    is_verified = models.BooleanField(
        default=True,
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


class PasswordResetRequest(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=False,
        related_name="password_reset_requests"
    )
    otp = models.CharField(max_length=255, default="123456")
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True)
