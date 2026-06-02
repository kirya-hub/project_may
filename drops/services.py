from __future__ import annotations

import datetime
import logging
import random
from datetime import timedelta
from typing import Literal

logger = logging.getLogger(__name__)

from django.db import transaction
from django.utils import timezone

from add_order.models import Order
from cafes.models import Cafe
from feed.models import FeedEvent
from promo.models import CouponOffer
from promo.services import generate_unique_code, get_active_drop_coupon
from user_profile.levels import add_xp
from user_profile.models import Profile, PromoCode

from .models import DropOption, DropWeek, week_start_for

RARITY_WEIGHTS_BASE: list[tuple[str, int]] = [
    (DropOption.Rarity.COMMON, 75),
    (DropOption.Rarity.RARE, 20),
    (DropOption.Rarity.LEGENDARY, 5),
]

LEVEL_BONUS_PERCENT = {
    (1, 3): 0,
    (4, 6): 5,
    (7, 9): 10,
    (10, 12): 15,
    (13, 14): 18,
    (15, 15): 25,
}


def _level_bonus(level: int) -> int:
    for (lo, hi), bonus in LEVEL_BONUS_PERCENT.items():
        if lo <= level <= hi:
            return bonus
    return 0


def get_user_tier_for_week(user, week_start) -> tuple[str | None, float]:
    """Тир и скорректированная сумма за конкретную неделю [week_start, week_start+7).

    Не фильтрует по минимальной сумме чека — считаем всё, кроме дублей.
    """
    from datetime import timedelta

    from django.db.models import Sum

    week_end = week_start + timedelta(days=7)
    result = Order.objects.filter(
        user=user,
        created_at__date__gte=week_start,
        created_at__date__lt=week_end,
        is_duplicate=False,
    ).aggregate(total=Sum('total_sum'))

    raw_sum = float(result['total'] or 0)
    if raw_sum <= 0:
        return None, 0.0

    try:
        profile = Profile.objects.get(user=user)
        level = int(profile.level or 1)
    except Profile.DoesNotExist:
        level = 1

    bonus = _level_bonus(level)
    adjusted = raw_sum * (1 + bonus / 100)

    if adjusted >= 2000:
        return 'GOLD', adjusted
    if adjusted >= 500:
        return 'BRONZE', adjusted
    return None, adjusted


def get_user_week_stats(user) -> tuple[str | None, float]:
    """Тир и скорректированная сумма за текущую неделю."""
    from datetime import date

    today = date.today()
    week_monday = today - timedelta(days=today.weekday())
    return get_user_tier_for_week(user, week_monday)


def get_user_tier(user) -> str | None:
    """Тир юзера за текущую неделю (обёртка для обратной совместимости)."""
    tier, _ = get_user_week_stats(user)
    return tier


DROP_EXPIRATION_DAYS = {
    DropOption.Rarity.COMMON: 5,
    DropOption.Rarity.RARE: 7,
    DropOption.Rarity.LEGENDARY: 14,
}

RARITY_FALLBACKS = {
    DropOption.Rarity.COMMON: [CouponOffer.Rarity.COMMON],
    DropOption.Rarity.RARE: [CouponOffer.Rarity.RARE, CouponOffer.Rarity.COMMON],
    DropOption.Rarity.LEGENDARY: [
        CouponOffer.Rarity.LEGENDARY,
        CouponOffer.Rarity.RARE,
        CouponOffer.Rarity.COMMON,
    ],
}


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


def _rarity_weights_for_profile(
    profile: Profile | None, tier: str = 'BRONZE'
) -> list[tuple[str, int]]:
    level = int(getattr(profile, 'level', 1) or 1) if profile else 1

    if tier == 'GOLD':
        if level >= 13:
            return [
                (DropOption.Rarity.COMMON, 45),
                (DropOption.Rarity.RARE, 38),
                (DropOption.Rarity.LEGENDARY, 17),
            ]
        if level >= 7:
            return [
                (DropOption.Rarity.COMMON, 55),
                (DropOption.Rarity.RARE, 33),
                (DropOption.Rarity.LEGENDARY, 12),
            ]
        return [
            (DropOption.Rarity.COMMON, 70),
            (DropOption.Rarity.RARE, 25),
            (DropOption.Rarity.LEGENDARY, 5),
        ]
    else:  # BRONZE
        if level >= 13:
            return [
                (DropOption.Rarity.COMMON, 65),
                (DropOption.Rarity.RARE, 35),
            ]
        if level >= 7:
            return [
                (DropOption.Rarity.COMMON, 75),
                (DropOption.Rarity.RARE, 25),
            ]
        return [
            (DropOption.Rarity.COMMON, 85),
            (DropOption.Rarity.RARE, 15),
        ]


def _pick_rarity(
    profile: Profile | None, tier: str = 'BRONZE', rng: random.Random | None = None
) -> str:
    return _weighted_choice(_rarity_weights_for_profile(profile, tier), rng=rng)


def _pick_reward_offer(
    cafe: Cafe | None,
    rarity: CouponOffer.Rarity,
    tier: str = 'BRONZE',
    rng: random.Random | None = None,
) -> CouponOffer | None:
    rng_obj = rng if rng is not None else random.Random()
    base_qs = CouponOffer.objects.filter(is_active=True, available_in_drop=True)

    fallbacks = RARITY_FALLBACKS.get(rarity, [CouponOffer.Rarity.COMMON])
    if tier == 'BRONZE':
        fallbacks = [r for r in fallbacks if r != CouponOffer.Rarity.LEGENDARY]

    for offer_rarity in fallbacks:
        qs = base_qs.filter(rarity=offer_rarity)
        if cafe is not None:
            cafe_qs = qs.filter(cafe=cafe)
            if cafe_qs.exists():
                qs = cafe_qs

        offers = list(qs.order_by('id')[:200])
        if offers:
            return rng_obj.choice(offers)
    return None


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


# ─── Фазы и хелперы ────────────────────────────────────────────────────────


def phase(week: DropWeek) -> Literal['ACCUMULATE', 'CLAIM', 'EXPIRED']:
    """Фаза по датам, независимо от статуса в БД."""
    today = timezone.localdate()
    if today >= week.claim_expires_at:
        return 'EXPIRED'
    if today >= week.expires_at:
        return 'CLAIM'
    return 'ACCUMULATE'


def _expire_if_needed(week: DropWeek) -> DropWeek:
    """Переводит в EXPIRED если вышло 14 дней. Обрабатывает и старый статус ACTIVE."""
    if week.status in (DropWeek.Status.COMPLETED, DropWeek.Status.EXPIRED):
        return week

    if timezone.localdate() >= week.claim_expires_at:
        week.status = DropWeek.Status.EXPIRED
        week.save(update_fields=['status'])
    return week


def _generate_options_for_week(week: DropWeek, user, tier: str) -> None:
    """Генерирует 3 опции для недели в фазе CLAIM. Вызывается не более одного раза."""
    profile, _ = Profile.objects.get_or_create(user=user)
    rng = random.Random(f'{user.pk}:{week.week_start.isoformat()}:{week.pk}')
    cafes = _pick_3_cafes_for_user(user, rng=rng)

    options: list[DropOption] = []
    for cafe in cafes:
        rarity = _pick_rarity(profile, tier=tier, rng=rng)
        reward_offer = _pick_reward_offer(cafe, rarity, tier=tier, rng=rng)
        options.append(
            DropOption(
                drop_week=week,
                cafe=cafe,
                rarity=rarity,
                reward_offer=reward_offer,
            )
        )

    DropOption.objects.bulk_create(options)


def expire_stale_drop_weeks(user) -> int:
    """Переводит все недели старше 14 дней в EXPIRED.

    _expire_if_needed обрабатывает только предыдущую неделю.
    Эта функция чистит всё накопившееся мусорное CHOOSING/ACTIVE.
    """
    today = timezone.localdate()
    cutoff = today - timedelta(days=14)
    return DropWeek.objects.filter(
        user=user,
        week_start__lte=cutoff,
        status__in=[DropWeek.Status.CHOOSING, DropWeek.Status.ACTIVE],
    ).update(status=DropWeek.Status.EXPIRED)


# ─── Резолверы недель ───────────────────────────────────────────────────────


def get_current_week(user) -> DropWeek:
    """Запись DropWeek для текущей недели. Создаёт если не существует."""
    start = week_start_for(timezone.now())
    week, _ = DropWeek.objects.get_or_create(user=user, week_start=start)
    return week


@transaction.atomic
def get_claimable_week(user) -> DropWeek | None:
    """Запись предыдущей недели, если она в периоде CLAIM и юзер заработал тир.

    Возвращает неделю со статусом CHOOSING (можно выбирать) или COMPLETED (уже выбрал).
    Возвращает None при EXPIRED, отсутствии тира или если запись не существует.
    Генерирует опции при первом входе в фазу CLAIM (если статус CHOOSING).
    """
    today = timezone.localdate()
    current_ws = today - timedelta(days=today.weekday())
    claimable_ws = current_ws - timedelta(days=7)

    try:
        week = DropWeek.objects.select_for_update().get(user=user, week_start=claimable_ws)
    except DropWeek.DoesNotExist:
        return None

    week = _expire_if_needed(week)

    if week.status == DropWeek.Status.EXPIRED:
        return None

    if phase(week) != 'CLAIM':
        return None

    tier, _ = get_user_tier_for_week(user, claimable_ws)
    if tier is None:
        return None

    if week.status == DropWeek.Status.CHOOSING and not week.options.exists():
        _generate_options_for_week(week, user, tier)

    return week


# ─── Выбор опции ────────────────────────────────────────────────────────────


@transaction.atomic
def choose_option(user, option_id: int) -> DropWeek:
    """Выбирает опцию, сразу выдаёт PromoCode, переводит неделю в COMPLETED."""
    option = DropOption.objects.select_for_update().get(pk=option_id, drop_week__user=user)
    week = DropWeek.objects.select_for_update().get(pk=option.drop_week_id)

    if phase(week) != 'CLAIM':
        return week
    if week.status != DropWeek.Status.CHOOSING:
        return week

    profile, _ = Profile.objects.select_for_update().get_or_create(user=user)

    earned_promocode = None
    if option.reward_offer_id:
        previous_drop = get_active_drop_coupon(profile)
        if previous_drop is not None:
            previous_drop.status = PromoCode.Status.EXPIRED
            previous_drop.save(update_fields=['status'])

        expires_at = timezone.localdate() + timedelta(days=DROP_EXPIRATION_DAYS[option.rarity])
        earned_promocode = PromoCode.objects.create(
            profile=profile,
            source_offer_id=option.reward_offer_id,
            origin=PromoCode.Origin.DROP,
            code=generate_unique_code(),
            description=option.reward_offer.description if option.reward_offer else '',
            expires_at=expires_at,
            status=PromoCode.Status.ACTIVE,
        )

    week.chosen_option = option
    week.status = DropWeek.Status.COMPLETED
    week.save(update_fields=['chosen_option', 'status'])

    FeedEvent.objects.create(
        user=user,
        kind=FeedEvent.Kind.DROP_CHOSEN,
        cafe=option.cafe,
        rarity=option.rarity,
        text=f'выбрал Drop: {option.cafe.name}',
        promocode=earned_promocode,
    )

    try:
        add_xp(user, 30)
    except Exception as exc:
        logger.warning('add_xp не удался для user=%s: %s', user.pk, exc)

    return week
