from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q, Prefetch

from products.services.product_service import ProductService
from services.util import CustomRequestUtil


class WishlistService(CustomRequestUtil, LoginRequiredMixin):

    def add_or_remove(self, payload):
        from products.models import Wishlist

        message = None
        error = None
        product = payload.get("product")

        wishlist_item, is_created = Wishlist.objects.get_or_create(
            user=self.auth_user,
            product_id=product,
        )

        if is_created:
            message = "Added to wishlist"
        else:
            self.hard_delete(wishlist_item)
            error = "Removed from wishlist"

        return message, error

    def fetch_list(self):
        from products.models import Wishlist
        product_service = ProductService(self.request)

        products_with_annotations = product_service.get_base_query()
        q = Q(user=self.auth_user)

        return Wishlist.objects.prefetch_related(
            Prefetch(
                'wishlist_items__product',
                queryset=products_with_annotations
            )
        ).filter(q).values(
            "product_id",
            product_name=F("product__name"), product_availability=F("product__availability"),
            product_price=F("product__price"), product_image=F("product__cover_image")

        ).order_by('-created_at')



    def hard_delete(self, wishlist_item):
        wishlist_item.delete()

        return wishlist_item, None
