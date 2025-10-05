from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    try:
        return d[int(key)]
    except (KeyError, ValueError, TypeError):
        return None
