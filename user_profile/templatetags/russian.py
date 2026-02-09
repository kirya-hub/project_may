from django import template

register = template.Library()

@register.filter
def ru_plural(value, forms: str):
    """
    forms: "друг,друга,друзей"
    """
    try:
        n = abs(int(value))
    except (TypeError, ValueError):
        return ""
    one, few, many = [x.strip() for x in forms.split(",")]
    n10 = n % 10
    n100 = n % 100
    if 11 <= n100 <= 14:
        return many
    if n10 == 1:
        return one
    if 2 <= n10 <= 4:
        return few
    return many
