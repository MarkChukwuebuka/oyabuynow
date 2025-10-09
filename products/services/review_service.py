from django.db.models import F, Q, Avg, Count
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

        product.rating = average_rating
        product.save(update_fields=['rating'])

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


def get_rating_breakdown(product):
    """
    Returns dict with counts and percentages for each star rating (5 to 1).

    """

    total_reviews = product.reviews.count()
    if total_reviews == 0:
        return {
            "total": 0,
            "ratings": {i: {"count": 0, "percent": 0} for i in range(5, 0, -1)}
        }

    # count reviews per rating
    counts = (
        product.reviews.values("rating")
        .annotate(count=Count("id"))
        .order_by("-rating")
    )

    result = {i: {"count": 0, "percent": 0} for i in range(5, 0, -1)}
    for entry in counts:
        rating = entry["rating"]
        count = entry["count"]
        percent = round((count / total_reviews) * 100, 2)
        result[rating] = {"count": count, "percent": percent}

    return {"total": total_reviews, "ratings": result}
