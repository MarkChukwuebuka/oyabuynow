import random
import string
from collections import defaultdict
from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count

from payments.models import Order, OrderItem
from services.util import CustomRequestUtil, send_email


def generate_order_ref(prefix="ORD"):
    """
    Generate a unique reference number for an order.

    Args:
        prefix (str): A prefix for the reference number (default is "ORD").

    Returns:
        str: A unique order reference number.
    """
    # Current timestamp in the format YYYYMMDDHHMMSS
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Random alphanumeric string of 6 characters
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # Combine prefix, timestamp, and random string
    ref_number = f"{prefix}-{timestamp}-{random_str}"

    return ref_number



class OrderService(CustomRequestUtil):

    def create_single(self, payload):
        order = Order.objects.create(
            user=self.auth_user,
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            email=payload.get("email"),
            state=payload.get("state"),
            address=payload.get("address"),
            phone=payload.get("phone"),
            lga=payload.get("lga"),
            ref=generate_order_ref()
        )

        return order


    def fetch_list(self, paginate=False):

        orders = self.get_base_query().order_by('-created_at').distinct()

        if paginate:
            paginator = Paginator(orders, 15)  # 25 items per page

            # get the current page number from request
            page_number = self.request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)

            return page_obj

        return orders

    def get_base_query(self):
        q = Q()
        if self.auth_user and not self.auth_vendor_profile:
            q &= Q(user=self.auth_user)
        if self.auth_vendor_profile:
            q &= Q(items__product__created_by=self.auth_user)

        qs = Order.objects.filter(q).select_related("user").prefetch_related("items")

        if self.auth_vendor_profile:
            qs = qs.annotate(
                items_count=Count('items', filter=Q(items__product__created_by=self.auth_user)),
                total_value=Sum('items__price', filter=Q(items__product__created_by=self.auth_user))
            )


        return qs

    def fetch_single_by_ref(self, ref):
        order = self.get_base_query().filter(ref=ref).first()
        if not order:
            return None, self.make_error("Order does not exist")

        return order, None


    def fetch_single_by_id(self, order_id):
        order = self.get_base_query().filter(id=order_id).first()
        if not order:
            return None, self.make_error("Order does not exist")

        return order, None


    # TODO: move to celery
    def group_order_items_by_vendor(self, order):
        vendor_items = defaultdict(list)

        # Group items by vendor email
        for item in order.items.select_related('product__created_by'):
            vendor_user = item.product.created_by
            vendor_email = getattr(vendor_user, 'vendor_profile', None)

            if vendor_email and getattr(vendor_email, 'business_email', None):
                email_key = vendor_email.business_email
            else:
                email_key = vendor_user.email

            vendor_items[email_key].append(item)

        # Send notification to each vendor
        for email, items in vendor_items.items():
            vendor_user = items[0].product.created_by
            vendor_profile = getattr(vendor_user, 'vendor_profile', None)

            email_context = {
                'ordered_items': items,
                'vendor_name': (
                        getattr(vendor_profile, 'business_name', None)
                        or getattr(vendor_profile, 'store_name', None)
                        or vendor_user.get_full_name()
                        or vendor_user.email
                ),
                'total_cost': sum(item.price for item in items),
                'order_ref': order.ref,
            }

            send_email(
                'emails/vendor-order-success.html',
                'Incoming Order',
                email,
                email_context
            )

        return None


class OrderItemService(CustomRequestUtil):

    def create_single(self, payload):

        order = OrderItem.objects.create(
            order=payload.get("order"),
            product=payload.get("product"),
            price=payload.get("price"),
            quantity=payload.get("state"),
        )

        return order, None

    def fetch_list(self, paginate=False):
        q = Q()

        order_items = self.get_base_query().filter(q).order_by('-created_at').distinct()

        if paginate:
            paginator = Paginator(order_items, 25)  # 25 items per page

            # get the current page number from request
            page_number = self.request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)

            return page_obj

        return order_items

    def get_base_query(self):
        q = Q()
        if self.auth_vendor_profile:
            q &= Q(product__created_by=self.auth_user)
        if self.auth_user and not self.auth_vendor_profile:
            q &= Q(order__user=self.auth_user)

        qs = OrderItem.objects.filter(q).select_related("product", "order")
        return qs


    def fetch_single(self, order_item_id):
        order_item = self.get_base_query().filter(id=order_item_id).first()
        if not order_item:
            return None, self.make_error("Order item does not exist")

        return order_item, None



