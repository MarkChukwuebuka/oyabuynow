from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views import View

from cart.services.cart_service import CartService
from products.models import Category
from products.services.product_service import ProductService
from services.util import CustomRequestUtil, send_email
from .models import Payment, OrderItem, Order, BankAccount

from django.http import JsonResponse

from .services.order_service import OrderService


def verify_payment(request, ref):
    # try:
    cart = CartService(request)
    payment = Payment.objects.filter(ref=ref).first()
    verified = payment.verify_payment()

    if verified:
        last_order = Order.objects.latest('created_at')

        if last_order:
            order = get_object_or_404(Order, pk=last_order.id)
            order.paid = True
            order.save()

            order_info = {
                'id': order.id,
                'total_cost': order.total_cost
            }

            context = {
                'placed_order': order_info,
                'payment': payment
            }
            cart.clear()
            return render(request, 'thank-you.html', context)
        else:
            messages.warning(request, 'Order ID not found')
            return JsonResponse({'error_message': 'Order ID not found'})
    else:
        messages.warning(request, 'Oops, your order was not processed, please contact support.')
        return redirect('/')
# except Payment.DoesNotExist:
#     messages.warning(request, 'Payment not found for this ref.')
#     return JsonResponse({'error_message': 'Payment not found.'})


@login_required
def check_out(request):

    bank = BankAccount.objects.filter(id=1).first()
    last_order = Order.objects.last()

    context = {
        "title":"Checkout",
        "bank": bank,
        "last_order": last_order
    }

    cart = CartService(request)
    current_user = request.user
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
            else:
                item_cost = product_instance.price * quantity_in_cart

            total_cost += item_cost

            order_item = OrderItem.objects.create(
                order=order,
                product=product_instance,
                price=item_cost,
                quantity=quantity_in_cart
            )
        #     TODO: update quantity sold

        payment = Payment.objects.create(
            amount=total_cost,
            email=current_user.email,
            user=current_user,
            order=order,
            ref=order.ref
        )

        order.total_cost = total_cost
        order.save()

        context = {
            'first_name': order.first_name,
            'last_name': order.last_name,
            'title': 'Thank You',
            'items' : OrderItem.objects.filter(order=order),
            'order': order,
            'ref': order.ref,
            'total_cost': total_cost,
            'payment': payment,
        }
        cart.clear()
        # send_email('emails/order-initiated.html', context, 'Order Initiated', 'whoisfreee@gmail.com')

        return render(request, 'frontend/order-success.html', context)

    return render(request, 'frontend/checkout.html', context)


class CreateListOrderView(View, CustomRequestUtil):
    extra_context_data = {
        "title": "Orders"
    }

    def get(self, request, *args, **kwargs):
        self.template_name = "backend/order-list.html"
        self.context_object_name = 'orders'

        order_service = OrderService(self.request)

        return self.process_request(
            request, target_function=order_service.fetch_list
        )



class RetrieveUpdateDeleteOrderView(View, CustomRequestUtil):
    extra_context_data = {
        "title": "Order Details"
    }

    def get(self, request, *args, **kwargs):
        self.template_name = "backend/order-details.html"
        self.context_object_name = 'order'

        order_service = OrderService(self.request)

        return self.process_request(
            request, target_function=order_service.fetch_single, ref=kwargs.get("ref")
        )
