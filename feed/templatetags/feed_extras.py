from django import template
from django.utils import timezone

register = template.Library()

MONTHS_RU = [
    'янв',
    'фев',
    'мар',
    'апр',
    'май',
    'июн',
    'июл',
    'авг',
    'сен',
    'окт',
    'ноя',
    'дек',
]


@register.filter
def smart_time(dt):
    if not dt:
        return ''

    now = timezone.localtime(timezone.now())
    dt = timezone.localtime(dt)

    diff = now - dt
    seconds = diff.total_seconds()
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = diff.days

    if minutes < 1:
        return 'только что'
    if minutes < 60:
        return f'{minutes} мин назад'
    if hours < 24:
        return f'{hours} ч назад'
    if days < 7:
        return f'{days} дн назад'

    month = MONTHS_RU[dt.month - 1]
    return f'{dt.day} {month}'
