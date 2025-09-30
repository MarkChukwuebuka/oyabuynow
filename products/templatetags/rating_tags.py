from django import template
import math
from products.models import Product

register = template.Library()


@register.inclusion_tag("./frontend/partials/rating_stars.html")
def show_rating(product=None, id=None, vendor_id=None):
    """
    Render star rating (supports half stars).

    Args:
      - product: Product instance (preferred).
      - id: Product ID (fallback if product not provided).
      - vendor_id: Optional vendor ID
    """
    if product is None and id:
        product = Product.objects.filter(id=id).first()

    # todo: handle vendor_id if needed

    rating = product.rating if product else None
    total_reviews = product.reviews.count() if product else 0


    if not rating:
        return {
            "full_stars": range(0),
            "half_star": False,
            "empty_stars": range(5),
            "rating": rating,
            "total_reviews": total_reviews,
        }

    else:
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
        }
