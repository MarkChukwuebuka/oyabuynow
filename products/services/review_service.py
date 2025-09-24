from django.db.models import F, Q, Avg
from django.utils import timezone

from services.util import CustomRequestUtil


class ProductReviewService(CustomRequestUtil):

    def create_single(self, payload):
        from products.models import ProductReview
        rating = payload.get("rating")
        review = payload.get("review")
        product = payload.get("product")

        product_review, is_created = ProductReview.objects.update_or_create(
            user=self.auth_user,
            product=product,
            defaults=dict(
                rating=rating,
                review=review,
            )
        )

        average_rating = ProductReview.objects.filter(product=product).aggregate(
            avg_rating=Avg("rating")
        )["avg_rating"]

        product.update(rating=average_rating)

        if not is_created:
            return "You've updated your review on this product", None

        message = "You've successfully reviewed this product"

        return message, None

    def fetch_list(self, product_id):
        from products.models import ProductReview
        q = Q(product_id=product_id)

        return ProductReview.objects.filter(q).values(
            "review", "rating", "updated_at",
            first_name=F("user__first_name"),
            last_name=F("user__last_name")
        ).order_by('-created_at')