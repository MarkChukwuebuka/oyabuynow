import random
import string
from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from payments.models import Order, OrderItem
from services.util import CustomRequestUtil


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

    def fetch_list(self):
        return self.get_base_query().filter(user=self.auth_user)

    def get_base_query(self):
        qs = Order.objects.select_related("user").prefetch_related("items")

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

        qs = OrderItem.objects.select_related("product", "order")
        return qs


    def fetch_single(self, order_item_id):
        order_item = self.get_base_query().filter(id=order_item_id).first()
        if not order_item:
            return None, self.make_error("Order item does not exist")

        return order_item, None