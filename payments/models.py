import uuid

from cloudinary.models import CloudinaryField
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import User
from crm.models import BaseModel
from products.models import Product
import secrets

from services.util import send_email


class OrderStatusChoices(models.TextChoices):
    ordered = 'Ordered'
    shipped = 'Shipped'
    delivered = 'Delivered'


class PaymentStatus(models.TextChoices):
    processing = 'Processing'
    paid = 'Paid'
    failed = 'Failed'


class Order(BaseModel):

    user = models.ForeignKey(User, related_name='orders', blank=True, null=True, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=250, blank=True, null=True)
    last_name = models.CharField(max_length=250, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    email = models.EmailField(max_length=250, blank=True, null=True)
    state = models.CharField(max_length=250, blank=True, null=True)
    lga = models.CharField(max_length=250, blank=True, null=True)
    phone = models.CharField(max_length=250, blank=True, null=True)
    paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=255, null=True, blank=True)
    refunded = models.BooleanField(default=False)
    total_cost = models.FloatField(default=0.0)
    ref = models.CharField(max_length=250, unique=True, blank=True, null=True)
    overall_status = models.CharField(
        max_length=25,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.ordered
    )
    payment_status = models.CharField(
        max_length=25,
        choices=PaymentStatus.choices,
        default=PaymentStatus.processing
    )

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user}'

    def amount_in_kobo(self):
        return self.total_cost * 100

    # def save(self, *args, **kwargs):
    #     if not self.ref:
    #         timestamp = timezone.now().strftime("%Y%m%d%H%M%S")  # e.g. 20251005123245
    #         random_part = uuid.uuid4().hex[:6].upper()  # e.g. A3F9C1
    #         self.ref = f"ORD-{timestamp}-{random_part}"
    #     super().save(*args, **kwargs)





class OrderItem(BaseModel):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    original_price = models.IntegerField(null=True)
    price = models.IntegerField(null=True)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=25, choices=OrderStatusChoices.choices, default=OrderStatusChoices.ordered)

    def __str__(self):
        return f'{self.order} - {self.product}'

    def save(self, *args, **kwargs):
        if self.pk is not None:
            old_order = OrderItem.objects.get(pk=self.pk)
            # Check if the status has changed to "shipped"
            context = {
                'name': self.order.first_name,
                'ref': self.order.ref,
            }
            if old_order.status != self.status and self.status == OrderStatusChoices.shipped:
                self.order.update_overall_status()
                pass
                # send_email('emails/order-shipped.html', context, 'Order Shipped', self.email)

            if old_order.status != self.status and self.status == OrderStatusChoices.delivered:
                self.order.update_overall_status()
                pass
                # send_email('emails/order-shipped.html', context, 'Order Shipped', self.email)

        super().save(*args, **kwargs)



class Payment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField(blank=True, null=True)
    ref = models.CharField(max_length=250)
    email = models.EmailField(max_length=250)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment')

    def __str__(self):
        return f"{self.user} - {self.amount}"

    def save(self, *args, **kwargs):
        # Check if the payment already exists
        if self.pk is not None:
            old_payment = Payment.objects.get(pk=self.pk)

            # Check if the `verified` status has changed
            if old_payment.verified != self.verified:
                if self.order:
                    # Update the `paid` field of the associated order
                    self.order.paid = self.verified
                    self.order.save()

                # Send email notification if `verified` is changed to True
                if self.verified:
                    context = {
                        'name': self.order.first_name,
                        'ref' : self.ref,
                        'amount' : self.amount
                    }
                    send_email('emails/payment-verified.html', context, 'Payment Verified', self.email)

        super().save(*args, **kwargs)


class Transaction(BaseModel):
    order = models.ForeignKey(Order, related_name="transactions", on_delete=models.CASCADE)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=25)
    amount = models.FloatField()
    gateway_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.order} - {self.reference} - {self.amount} - {self.status}"