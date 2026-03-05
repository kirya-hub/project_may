from __future__ import annotations

import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from add_order.models import Order
from cafes.models import Cafe
from promo.models import CouponOffer
from user_profile.models import Profile

from .models import DropOption, DropWeek, week_start_for

RARITY_WEIGHTS_BASE: list[tuple[str, int]] = [
    (DropOption.Rarity.COMMON, 75),
    (DropOption.Rarity.RARE, 20),
    (DropOption.Rarity.LEGENDARY, 5),
]


def weighted_choice(items: list[tuple[str, int]]) -> str:
    total = 0
    for _, w in items:
        total += w
    r = random.randint(1, total)
    acc = 0
    for value, weight in items:
        acc += weight
        if r <= acc:
            return value
    return items[-1][0]


def get_rarity_weights_for_user(profile: Profile | None) -> list[tuple[str, int]]:
    if profile is None:
        return RARITY_WEIGHTS_BASE

    level = getattr(profile, 'level', 1) or 1
    bump = min(level // 5, 10)

    common = max(55, 75 - bump * 2)
    rare = min(35, 20 + bump * 2)
    legendary = min(10, 5 + bump)

    total = common + rare + legendary
    if total != 100:
        common += 100 - total

    return [
        (DropOption.Rarity.COMMON, common),
        (DropOption.Rarity.RARE, rare),
        (DropOption.Rarity.LEGENDARY, legendary),
    ]


def pick_rarity_for_profile(profile: Profile | None) -> str:
    weights = get_rarity_weights_for_user(profile)
    return weighted_choice(weights)


def pick_offer_for_rarity(rarity: str) -> CouponOffer:
    qs = CouponOffer.objects.filter(is_active=True, rarity=rarity)
    if not qs.exists():
        qs = CouponOffer.objects.filter(is_active=True)
    offers = list(qs)
    return random.choice(offers)


def get_or_create_current_week(profile: Profile) -> DropWeek:
    start = week_start_for(timezone.now())
    week, _ = DropWeek.objects.get_or_create(
        profile=profile,
        week_start=start,
        defaults={'expires_at': start + timedelta(days=7)},
    )
    return week


def get_or_create_week(user_or_profile):
    if isinstance(user_or_profile, Profile):
        return get_or_create_current_week(user_or_profile)
    profile = Profile.objects.get(user=user_or_profile)
    return get_or_create_current_week(profile)


def _seen_cafe_ids(profile: Profile) -> set[int]:
    return set(
        Order.objects.filter(user=profile.user, status=Order.Status.CONFIRMED)
        .values_list('cafe_id', flat=True)
        .distinct()
    )


def _candidate_cafes(profile: Profile) -> tuple[list[Cafe], list[Cafe]]:
    seen = _seen_cafe_ids(profile)
    all_cafes = list(Cafe.objects.all())
    new_cafes = [c for c in all_cafes if c.id not in seen]
    old_cafes = [c for c in all_cafes if c.id in seen]
    return new_cafes, old_cafes


def _pick_cafe_for_drop(profile: Profile, prefer_new: bool) -> Cafe | None:
    new_cafes, old_cafes = _candidate_cafes(profile)

    if prefer_new and new_cafes:
        return random.choice(new_cafes)

    pool = old_cafes or new_cafes
    if not pool:
        return None
    return random.choice(pool)


def generate_options_for_week(week: DropWeek) -> list[DropOption]:
    profile = week.profile

    new_cafes, _ = _candidate_cafes(profile)

    if len(new_cafes) >= 2:
        prefer_flags = [True, True, False]
    elif len(new_cafes) == 1:
        prefer_flags = [True, False, False]
    else:
        prefer_flags = [False, False, False]

    random.shuffle(prefer_flags)

    options: list[DropOption] = []
    used_cafe_ids: set[int] = set()

    for prefer_new in prefer_flags:
        cafe = _pick_cafe_for_drop(profile, prefer_new=prefer_new)

        if cafe and cafe.id in used_cafe_ids:
            for _ in range(5):
                alt = _pick_cafe_for_drop(profile, prefer_new=prefer_new)
                if alt and alt.id not in used_cafe_ids:
                    cafe = alt
                    break

        if cafe is None:
            continue

        used_cafe_ids.add(cafe.id)

        rarity = pick_rarity_for_profile(profile)
        offer = pick_offer_for_rarity(rarity)

        options.append(
            DropOption(
                week=week,
                cafe=cafe,
                offer=offer,
                rarity=rarity,
            )
        )

    DropOption.objects.bulk_create(options)
    return options


def ensure_week_options(profile: Profile) -> DropWeek:
    week = get_or_create_current_week(profile)

    if week.status in (DropWeek.Status.COMPLETED, DropWeek.Status.EXPIRED):
        return week

    if not week.options.exists():
        generate_options_for_week(week)

    return week


@transaction.atomic
def choose_option(profile: Profile, option_id: int) -> DropWeek:
    week = ensure_week_options(profile)

    option = DropOption.objects.select_for_update().get(id=option_id, week=week)
    week.chosen_option = option
    week.status = DropWeek.Status.CHOOSEN
    week.save(update_fields=['chosen_option', 'status'])
    return week


@transaction.atomic
def try_complete_by_order(order: Order) -> bool:
    if order.status != Order.Status.CONFIRMED:
        return False

    profile = Profile.objects.select_for_update().get(user=order.user)
    week = ensure_week_options(profile)

    if week.status != DropWeek.Status.CHOOSEN:
        return False

    if not week.chosen_option:
        return False

    if week.chosen_option.cafe_id != order.cafe_id:
        return False

    week.status = DropWeek.Status.COMPLETED
    week.completed_at = timezone.now()
    week.completed_order = order
    week.save(update_fields=['status', 'completed_at', 'completed_order'])
    return True
