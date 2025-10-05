from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q, Prefetch, OuterRef, Subquery, Case, When, ExpressionWrapper, DecimalField

from media.models import Upload
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
            message = "Removed from wishlist"

        return message, error

    def fetch_list(self):
        from products.models import Wishlist
        product_service = ProductService(self.request)

        products_with_annotations = product_service.get_base_query()
        q = Q(user=self.auth_user)

        first_media = Upload.objects.filter(
            product=OuterRef("product_id")
        ).order_by("created_at").values("image")[:1]

        return Wishlist.objects.filter(q).annotate(
            first_media=Subquery(first_media),
            discounted_price=Case(
                When(
                    product__percentage_discount__isnull=False,
                    product__percentage_discount__gt=0,
                    then=ExpressionWrapper(
                        F('product__price')
                        - ((F('product__percentage_discount') * F("product__price")) / 100),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    ),
                ),
                default=F("product__price"),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
        ).values(
            "product_id",
            name=F("product__name"), stock=F("product__stock"),
            price=F("product__price"), slug=F("product__slug"),
            first_media=F("first_media"), category=F("product__category__name"),
            discounted_price=F("discounted_price"),
            percentage_discount=F("product__percentage_discount")

        ).order_by('-created_at')



    def hard_delete(self, wishlist_item):
        wishlist_item.delete()

        return wishlist_item, None
