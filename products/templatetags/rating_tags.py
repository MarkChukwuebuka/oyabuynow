from django import template
import math

register = template.Library()

@register.inclusion_tag("./frontend/partials/rating_stars.html")
def show_rating(rating):
    """
    Render star rating (supports half stars).
    rating: float 0–5
    """
    full_stars = int(math.floor(rating))
    half_star = (rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)

    return {
        "full_stars": range(full_stars),
        "half_star": half_star,
        "empty_stars": range(empty_stars),
        "rating": rating,
    }
