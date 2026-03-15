from __future__ import annotations

from django import template

from user_profile.models import Profile

register = template.Library()


@register.filter(name='user_level')
def user_level(user) -> int:
    if not user:
        return 1

    profile = getattr(user, 'profile', None)
    if profile is None:
        profile, _ = Profile.objects.get_or_create(user=user)

    return int(getattr(profile, 'level', 1) or 1)


@register.filter(name='level_tier')
def level_tier(value) -> str:
    try:
        level = int(value or 1)
    except (TypeError, ValueError):
        level = 1

    if level >= 15:
        return 'max'
    if level >= 10:
        return 'high'
    if level >= 5:
        return 'mid'
    return 'base'


@register.simple_tag(name='user_level')
def user_level_tag(user) -> int:
    return user_level(user)
