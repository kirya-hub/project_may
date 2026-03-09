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


@register.simple_tag(name='user_level')
def user_level_tag(user) -> int:

    return user_level(user)
