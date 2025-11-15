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


@register.filter
def is_panel_denuncias(path):
    """Return ``True`` when the request path belongs to ``panel/denuncias``.

    The view for the denuncias panel renders several nested URLs (for example
    ``/panel/denuncias/`` and ``/panel/denuncias/42/``).  Django templates do
    not allow calling Python methods such as ``request.path.startswith``
    directly, so we provide a tiny helper filter that keeps that logic in one
    place and can be reused across templates.
    """

    if not path:
        return False

    path_str = str(path)
    prefix = "/panel/denuncias/"

    return path_str == prefix.rstrip("/") or path_str.startswith(prefix)
