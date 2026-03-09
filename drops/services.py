from __future__ import annotations

import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from add_order.models import Order
from cafes.models import Cafe
from feed.models import FeedEvent
from promo.models import CouponOffer
from user_profile.levels import add_xp
from user_profile.models import Profile, PromoCode

from .models import DropOption, DropWeek, week_start_for

RARITY_WEIGHTS_BASE: list[tuple[str, int]] = [
    (DropOption.Rarity.COMMON, 75),
    (DropOption.Rarity.RARE, 20),
    (DropOption.Rarity.LEGENDARY, 5),
]


def _weighted_choice(items: list[tuple[str, int]], rng: random.Random | None = None) -> str:
    rng_obj = rng if rng is not None else random.Random()
    total = sum(w for _, w in items)
    r = rng_obj.randint(1, max(1, total))
    acc = 0
    for value, weight in items:
        acc += weight
        if r <= acc:
            return value
    return items[-1][0]


def _rarity_weights_for_profile(profile: Profile | None) -> list[tuple[str, int]]:
    if profile is None:
        return RARITY_WEIGHTS_BASE

    level = int(getattr(profile, 'level', 1) or 1)
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


def _pick_rarity(profile: Profile | None, rng: random.Random | None = None) -> str:
    return _weighted_choice(_rarity_weights_for_profile(profile), rng=rng)


def _pick_reward_offer(cafe: Cafe | None, rng: random.Random | None = None) -> CouponOffer | None:
    rng_obj = rng if rng is not None else random.Random()
    qs = CouponOffer.objects.filter(is_active=True)

    if cafe is not None:
        cafe_qs = qs.filter(cafe=cafe)
        if cafe_qs.exists():
            qs = cafe_qs

    offers = list(qs[:200])
    if not offers:
        return None
    return rng_obj.choice(offers)


def _seen_cafe_ids(user) -> set[int]:
    return set(
        Order.objects.filter(user=user)
        .exclude(cafe__isnull=True)
        .values_list('cafe_id', flat=True)
        .distinct()
    )


def _pick_3_cafes_for_user(user, rng: random.Random | None = None) -> list[Cafe]:
    rng_obj = rng if rng is not None else random.Random()
    all_cafes = list(Cafe.objects.all())
    if not all_cafes:
        return []

    seen = _seen_cafe_ids(user)
    new_cafes = [c for c in all_cafes if c.id not in seen]
    old_cafes = [c for c in all_cafes if c.id in seen]

    picks: list[Cafe] = []

    if len(new_cafes) >= 2:
        picks.extend(rng_obj.sample(new_cafes, 2))
    elif len(new_cafes) == 1:
        picks.append(new_cafes[0])

    if old_cafes and len(picks) < 3:
        pool = [c for c in old_cafes if c.id not in {p.id for p in picks}]
        if pool:
            picks.append(rng_obj.choice(pool))

    remaining = [c for c in all_cafes if c.id not in {p.id for p in picks}]
    while remaining and len(picks) < 3:
        c = rng_obj.choice(remaining)
        picks.append(c)
        remaining = [x for x in remaining if x.id != c.id]

    return picks[:3]


def _get_or_create_week(user) -> DropWeek:
    start = week_start_for(timezone.now())
    week, _ = DropWeek.objects.get_or_create(user=user, week_start=start)
    return week


def _expire_if_needed(week: DropWeek) -> DropWeek:
    if week.status in (DropWeek.Status.COMPLETED, DropWeek.Status.EXPIRED):
        return week

    if timezone.localdate() >= week.expires_at:
        week.status = DropWeek.Status.EXPIRED
        week.save(update_fields=['status'])
    return week


@transaction.atomic
def ensure_week_options(user) -> DropWeek:
    week = DropWeek.objects.select_for_update().get(pk=_get_or_create_week(user).pk)
    week = _expire_if_needed(week)

    if week.status in (DropWeek.Status.COMPLETED, DropWeek.Status.EXPIRED):
        return week

    if not week.options.exists():
        profile, _ = Profile.objects.get_or_create(user=user)
        rng = random.Random(f'{user.pk}:{week.week_start.isoformat()}')
        cafes = _pick_3_cafes_for_user(user, rng=rng)

        options: list[DropOption] = []
        for cafe in cafes:
            rarity = _pick_rarity(profile, rng=rng)
            reward_offer = _pick_reward_offer(cafe, rng=rng)
            options.append(
                DropOption(
                    drop_week=week,
                    cafe=cafe,
                    rarity=rarity,
                    reward_offer=reward_offer,
                )
            )

        DropOption.objects.bulk_create(options)

    return week


@transaction.atomic
def choose_option(user, option_id: int) -> DropWeek:
    week = ensure_week_options(user)
    week = DropWeek.objects.select_for_update().get(pk=week.pk)

    if week.status != DropWeek.Status.CHOOSING:
        return week

    option = DropOption.objects.select_for_update().get(pk=option_id, drop_week=week)

    week.chosen_option = option
    week.status = DropWeek.Status.ACTIVE
    week.save(update_fields=['chosen_option', 'status'])

    FeedEvent.objects.create(
        user=user,
        kind=FeedEvent.Kind.DROP_CHOSEN,
        cafe=option.cafe,
        text=f'выбрал Drop: {option.cafe.name}',
    )

    return week


@transaction.atomic
def try_complete_by_order(order: Order) -> bool:
    if order.cafe_id is None:
        return False

    week = _get_or_create_week(order.user)
    week = DropWeek.objects.select_for_update().get(pk=week.pk)
    week = _expire_if_needed(week)

    if week.status != DropWeek.Status.ACTIVE:
        return False
    if not week.chosen_option_id:
        return False

    chosen = DropOption.objects.select_for_update().get(pk=week.chosen_option_id)
    if chosen.cafe_id != order.cafe_id:
        return False

    profile, _ = Profile.objects.select_for_update().get_or_create(user=order.user)

    if chosen.reward_offer_id:
        already = PromoCode.objects.filter(
            profile=profile,
            source_offer_id=chosen.reward_offer_id,
            acquired_at__date__gte=week.week_start,
        ).exists()

        if not already:
            from promo.services import generate_unique_code

            PromoCode.objects.create(
                profile=profile,
                source_offer_id=chosen.reward_offer_id,
                code=generate_unique_code(),
                description=chosen.reward_offer.description if chosen.reward_offer else '',
                expires_at=(
                    timezone.localdate() + timedelta(days=int(chosen.reward_offer.expires_in_days))
                    if chosen.reward_offer and chosen.reward_offer.expires_in_days
                    else None
                ),
                status=PromoCode.Status.ACTIVE,
            )

    week.status = DropWeek.Status.COMPLETED
    week.save(update_fields=['status'])

    try:
        add_xp(order.user, 15)
    except Exception:
        pass

    return True
