"""Custom template filters for request-related helpers."""

from django import template

register = template.Library()


@register.filter
def startswith(value, prefix):
    """Return True if ``value`` starts with ``prefix``.

    Both value and prefix are coerced to strings so the filter is safe to use
    with paths or other objects that define ``__str__``. ``None`` values
    short-circuit to ``False``.
    """

    if value is None or prefix is None:
        return False
    return str(value).startswith(str(prefix))
