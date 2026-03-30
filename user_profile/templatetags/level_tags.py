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
    """
    Возвращает CSS-суффикс для .level-badge--<tier>:
      1–3   → black   (чёрный)
      4–7   → blue    (синий)
      8–12  → purple  (фиолетовый)
      13+   → gold    (золотой)
    """
    try:
        level = int(value or 1)
    except (TypeError, ValueError):
        level = 1

    if level >= 13:
        return 'gold'
    if level >= 8:
        return 'purple'
    if level >= 4:
        return 'blue'
    return 'black'


@register.simple_tag(name='user_level_tag')
def user_level_tag(user) -> int:
    return user_level(user)
