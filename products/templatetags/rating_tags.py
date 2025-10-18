from django import template
import math
from products.models import Product, ProductReview
from products.services.review_service import get_rating_breakdown

register = template.Library()


@register.inclusion_tag("./frontend/partials/rating_stars.html")
def show_rating(product=None, id=None, vendor=None, show_count=True, rating=None):
    """
    Render star rating (supports half stars).

    Args:
        product: Product instance (preferred).
        id: Product ID (fallback if product not provided).
        vendor: Optional vendor (placeholder for vendor-specific ratings).
        show_count: Whether to include total reviews count (default: True).
        rating: Explicit rating value (overrides product.rating if provided).
    """

    # ✅ Resolve product if rating not explicitly provided
    if rating is None:
        if product is None and id:
            product = Product.objects.filter(id=id).first()

        # TODO: handle vendor_id logic if required
        rating = getattr(product, "rating", None)
        total_reviews = product.reviews.count() if (product and show_count) else 0

    else:
        # Explicit rating passed — don’t query product unless needed
        total_reviews = 0
        if product:
            total_reviews = product.reviews.count() if show_count else 0

        if vendor:
            total_reviews = ProductReview.available_objects.filter(
                product__created_by=vendor.user
            ).count()

    # ✅ No rating available → return 5 empty stars
    if not rating:
        return {
            "full_stars": range(0),
            "half_star": False,
            "empty_stars": range(5),
            "rating": None,
            "total_reviews": total_reviews,
            "show_count": show_count,
        }

    # ✅ Normalize to nearest 0.5
    rating = round(rating * 2) / 2
    full_stars = int(math.floor(rating))
    half_star = (rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)

    return {
        "full_stars": range(full_stars),
        "half_star": half_star,
        "empty_stars": range(empty_stars),
        "rating": rating,
        "total_reviews": total_reviews,
        "show_count": show_count,
    }



@register.inclusion_tag("./frontend/partials/rating_breakdown.html")
def show_rating_breakdown(product):
    breakdown = get_rating_breakdown(product)
    return {
        "total_reviews": breakdown["total"],
        "ratings": breakdown["ratings"],
    }