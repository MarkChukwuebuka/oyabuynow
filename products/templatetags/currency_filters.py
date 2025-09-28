from django import template

register = template.Library()

@register.filter
def naira(value):
    """
    Format number as Nigerian Naira currency (₦1,000 or ₦1,000.50).
    """
    try:
        value = float(value)
        # If the number is whole, drop decimals
        if value.is_integer():
            return f"₦{int(value):,}"
        return f"₦{value:,.2f}"
    except (ValueError, TypeError):
        return value
