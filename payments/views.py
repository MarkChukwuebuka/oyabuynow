import json

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect

from django.views import View
from django.views.decorators.csrf import csrf_exempt

from cart.services.cart_service import CartService
from products.services.product_service import ProductService
from services.util import CustomRequestUtil, customer_required
from .models import OrderItem, Order, PaymentStatus, Transaction, OrderStatusChoices
from crm.tasks import send_email_notification
from .services.order_service import OrderService


@login_required
def paystack_verify_payment(request, order_id):
    cart = CartService(request)
    order_service = OrderService(request)
    product_service = ProductService(request)
    order, _ = order_service.fetch_single_by_id(order_id)
    if not order:
        return redirect("checkout")

    reference = request.GET.get("reference", "")
    payment_method = request.GET.get("payment_method", "")

    if not reference:
        return redirect(f"/payment-status/{order.id}/?payment_status=Failed")

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers=headers
    )

    response_data = response.json()


    Transaction.objects.create(
        order=order,
        reference=reference,
        status=response_data["data"]["status"],
        amount=response_data["data"]["amount"] / 100,
        gateway_response=response_data,
    )

    if response_data.get("status") and response_data["data"]["status"] == "success":
        amount_paid = response_data["data"]["amount"] / 100
        if abs(amount_paid - order.total_cost) < 1:
            if order.payment_status == PaymentStatus.processing:
                order.payment_status = PaymentStatus.paid
                order.payment_method = payment_method
                order.ref = reference
                order.save(update_fields=["payment_status", "payment_method", "ref"])
                cart.clear()
                del request.session['order_id']

                for item in order.items.all():
                    product_service.update_quantity_sold(item.product, item.quantity)

                email_context = {
                    'customer_name' : order.first_name,
                    'order' : order
                }

                # email customer
                send_email_notification.delay(
                    'emails/order-success.html', 'Order Success', order.email, email_context
                )

                # group and email the vendor(s)
                order_service.group_order_items_by_vendor(order)

                return redirect(f"/payment-status/{order.id}/?payment_status=Paid")

    return redirect(f"/payment-status/{order.id}/?payment_status=Failed")



class OrderSuccessView(LoginRequiredMixin, View, CustomRequestUtil):
    extra_context_data = {
        "title": "Order Success"
    }

    def get(self, request, *args, **kwargs):
        self.template_name = "frontend/order-success.html"
        self.context_object_name = 'order'

        payment_status = request.GET.get("payment_status")

        if payment_status == "Failed":
            request.session["order_id"] = kwargs.get("order_id")
            return redirect("/confirm-order/")

        order_service = OrderService(self.request)

        return self.process_request(
            request, target_function=order_service.fetch_single_by_id, order_id=kwargs.get("order_id")
        )



@login_required
def check_out(request):

    if not request.session.get("cart"):
        messages.error(request, "There are no items in your cart")
        return redirect("home")


    last_order = Order.objects.last()

    context = {
        "title":"Checkout",
        "last_order": last_order
    }

    cart = CartService(request)
    product_service = ProductService(request)

    if request.method == 'POST':
        payload = dict(
            first_name = request.POST.get("first_name"),
            last_name = request.POST.get("last_name"),
            email = request.POST.get("email"),
            lga = request.POST.get("lga"),
            address = request.POST.get("address"),
            state = request.POST.get("state"),
            phone = request.POST.get("phone"),
        )

        order = OrderService(request).create_single(payload)



        total_cost = 0

        for item in cart:
            product_in_cart = item['product']
            quantity_in_cart = item['quantity']

            product_instance, error = product_service.fetch_single(product_in_cart.id)
            if error:
                pass

            if product_instance.percentage_discount:
                item_cost = product_instance.discounted_price * quantity_in_cart
                original_price = product_instance.discounted_price
            else:
                item_cost = product_instance.price * quantity_in_cart
                original_price = product_instance.price

            total_cost += item_cost

            OrderItem.objects.create(
                order=order,
                product=product_instance,
                original_price=original_price,
                price=item_cost,
                quantity=quantity_in_cart,

            )

        order.total_cost = total_cost
        order.save()

        request.session["order_id"] = order.id

        return redirect("confirm-order")

    return render(request, 'frontend/checkout.html', context)


class ConfirmOrderView(LoginRequiredMixin, View, CustomRequestUtil):
    extra_context_data = {
        "title": "Confirm orders"
    }

    def get(self, request, *args, **kwargs):
        self.template_name = "frontend/confirm-order.html"
        self.context_object_name = 'order'
        order_id = request.session.get("order_id")

        if not request.session.get("cart"):
            messages.error(request, "There are no items in your cart")

            return redirect("home")

        self.extra_context_data['paystack_public_key'] = settings.PAYSTACK_PUBLIC_KEY

        order_service = OrderService(self.request)

        return self.process_request(
            request, target_function=order_service.fetch_single_by_id, order_id=order_id
        )


class CreateListOrderView(View, CustomRequestUtil):
    extra_context_data = {
        "title": "Orders"
    }
    @customer_required
    def get(self, request, *args, **kwargs):
        self.template_name = "backend/order-list.html"
        self.context_object_name = 'orders'

        order_service = OrderService(self.request)

        return self.process_request(
            request, target_function=order_service.fetch_list
        )



class RetrieveUpdateDeleteOrderView(View, CustomRequestUtil):
    template_name = "backend/order-detail.html"
    extra_context_data = {
        "title": "Order Details"
    }

    def get(self, request, *args, **kwargs):
        self.context_object_name = 'order'

        order_service = OrderService(self.request)

        return self.process_request(
            request, target_function=order_service.fetch_single_by_ref, ref=kwargs.get("ref")
        )


@csrf_exempt
def update_order_item_status(request):
    order_service = OrderService(request)

    if request.method == "POST":
        data = json.loads(request.body)
        order_id = data.get("order_id")
        action = data.get("action")

        order, _ = order_service.fetch_single_by_id(order_id)
        if not order:
            return JsonResponse({
                "success": False,
                "message": _
            })

        order_items = OrderItem.available_objects.filter(order=order, product__created_by=request.user)

        if action == "shipped":

            for item in order_items:
                item.status = OrderStatusChoices.shipped
                item.save()

            message = "This order has been marked as 'Shipped'."

            return JsonResponse({
                "success": True,
                "message": message,
            })

        elif action == "delivered":
            for item in order_items:
                item.status = OrderStatusChoices.delivered
                item.save()

            message = "This order has been marked as 'Delivered'."

            return JsonResponse({
                "success": True,
                "message": message,
            })
        else:
            message = "An error occurred while trying to process this request."

        return JsonResponse({
            "success": False,
            "message": message,
        })
    return None
