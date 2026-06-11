from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return dict[key] — used in calendar to get completion label for a date."""
    return dictionary.get(key, '')

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter — used for weekday headers."""
    return value.split(delimiter)
