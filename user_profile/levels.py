from __future__ import annotations

from django.utils import timezone

from .models import Profile

MAX_LEVEL = 15

LEGENDARY_BY_LEVEL = [4, 5, 5, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 8]


def xp_needed_for_level(level: int) -> int:
    if level <= 1:
        return 40
    if level == 2:
        return 60
    if level == 3:
        return 85
    if level == 4:
        return 120
    x = level - 4
    return 120 + x * 55 + x * x * 10


def get_or_create_profile(user) -> Profile:
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def add_xp(user, amount: int) -> Profile:
    if amount <= 0:
        return get_or_create_profile(user)

    profile = Profile.objects.select_for_update().get_or_create(user=user)[0]

    profile.xp = (profile.xp or 0) + amount

    if profile.level >= MAX_LEVEL:
        profile.save(update_fields=['xp'])
        return profile

    while profile.level < MAX_LEVEL:
        need = xp_needed_for_level(profile.level)
        if profile.xp < need:
            break
        profile.xp -= need
        profile.level += 1

    profile.save(update_fields=['xp', 'level'])
    return profile


def grant_trade_xp_once_per_day(user, amount: int) -> bool:
    if amount <= 0:
        return False

    today = timezone.localdate()
    profile = get_or_create_profile(user)

    if profile.last_trade_xp_date == today:
        return False

    profile.last_trade_xp_date = today
    profile.save(update_fields=['last_trade_xp_date'])

    add_xp(user, amount)
    return True
