from __future__ import annotations

from django import template

from user_profile.models import Profile

register = template.Library()


@register.filter(name='user_level')
def user_level(user) -> int:
    if not user:
        return 1
    profile, _ = Profile.objects.get_or_create(user=user)
    return int(profile.level or 1)
