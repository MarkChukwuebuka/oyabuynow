import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

from accounts.models import User
from crm.models import BaseModel
from products.models import Product

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

    def update_overall_status(self):
        """Auto-update overall status based on items."""
        item_statuses = self.items.values_list("status", flat=True)
        if all(s == OrderStatusChoices.shipped for s in item_statuses):
            self.overall_status = OrderStatusChoices.shipped
        elif all(s == OrderStatusChoices.delivered for s in item_statuses):
            self.overall_status = OrderStatusChoices.delivered
        else:
            self.overall_status = OrderStatusChoices.ordered
        self.save()



class OrderItem(BaseModel):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    original_price = models.IntegerField(null=True)
    price = models.IntegerField(null=True)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=25, choices=OrderStatusChoices.choices, default=OrderStatusChoices.ordered)
    ref = models.CharField(max_length=50, null=True, blank=True)
    estimated_delivery_date_down = models.DateField(null=True, blank=True)
    estimated_delivery_date_up = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.order} - {self.product}'

    def save(self, *args, **kwargs):
        if not self.estimated_delivery_date_down or not self.estimated_delivery_date_up:
            base_date = getattr(self, 'created_at', timezone.now())
            self.estimated_delivery_date_down = base_date + timedelta(days=7)
            self.estimated_delivery_date_up = base_date + timedelta(days=9)

        order_ref = self.order.ref
        if order_ref:
            if self.ref:
                if order_ref != self.ref.split("-ITM-")[0]:
                    self.ref = f"{order_ref}-ITM-{self.pk}"
            else:
                self.ref = f"{order_ref}-ITM-{self.pk}"

        if self.pk is not None:
            old_order_item = OrderItem.objects.get(pk=self.pk)

            email_context = {
                'customer_name': self.order.first_name,
                'order_item' : old_order_item,
            }

            if old_order_item.status != self.status and self.status == OrderStatusChoices.shipped:
                self.order.update_overall_status()

                # send_email(
                #     'emails/order-shipped.html', 'Order Shipped', self.order.email, email_context
                # )

            if old_order_item.status != self.status and self.status == OrderStatusChoices.delivered:
                self.order.update_overall_status()

                # send_email(
                #     'emails/order-delivered.html', 'Order Delivered', self.order.email, email_context
                # )

        super().save(*args, **kwargs)




class Transaction(BaseModel):
    order = models.ForeignKey(Order, related_name="transactions", on_delete=models.CASCADE)
    reference = models.CharField(max_length=100)
    status = models.CharField(max_length=25)
    amount = models.FloatField()
    gateway_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.order} - {self.reference} - {self.amount} - {self.status}"