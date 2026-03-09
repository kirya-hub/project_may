from __future__ import annotations

from django import template
from django.utils import timezone

from drops.models import DropWeek, week_start_for

register = template.Library()


@register.simple_tag(name='drop_has_new')
def drop_has_new(user) -> bool:

    if not user or not getattr(user, 'is_authenticated', False):
        return False

    start = week_start_for(timezone.now())
    week = DropWeek.objects.filter(user=user, week_start=start).only('status').first()

    if week is None:
        return True

    return week.status == DropWeek.Status.CHOOSING
