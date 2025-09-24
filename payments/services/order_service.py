import random
import string
from datetime import datetime

from django.utils import timezone

from payments.models import Order
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
        qs = Order.objects.select_related("user").prefetch_related("items__product")

        return qs

    def fetch_single(self, ref):
        order = self.get_base_query().filter(ref=ref).first()
        if not order:
            return None, self.make_error("Order does not exist")

        return order, None