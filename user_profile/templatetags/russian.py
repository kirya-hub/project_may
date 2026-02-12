from django import template

register = template.Library()


@register.filter(name="russian")
def russian(value, forms: str):
    """
    Склонение по числу.
    forms: "друг,друга,друзей"
    usage: {{ n|russian:"друг,друга,друзей" }}
    """
    try:
        n = abs(int(value))
    except (TypeError, ValueError):
        return forms.split(",")[-1].strip()

    f = [x.strip() for x in forms.split(",")]
    if len(f) != 3:
        return forms

    if 11 <= (n % 100) <= 14:
        return f[2]

    last = n % 10
    if last == 1:
        return f[0]
    if 2 <= last <= 4:
        return f[1]
    return f[2]
