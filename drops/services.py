from __future__ import annotations

import random

from django.db import transaction
from django.utils import timezone

from add_order.models import Order
from cafes.models import Cafe
from promo.models import CouponOffer
from user_profile.models import Profile, PromoCode

from .models import DropOption, DropWeek, week_start_for

RARITY_WEIGHTS = [
    (DropOption.Rarity.COMMON, 75),
    (DropOption.Rarity.RARE, 20),
    (DropOption.Rarity.LEGENDARY, 5),
]


def pick_rarity() -> str:
    items: list[str] = []
    for r, w in RARITY_WEIGHTS:
        items.extend([r] * w)
    return random.choice(items)


def pick_reward_offer(cafe: Cafe, rarity: str) -> CouponOffer | None:
    qs = CouponOffer.objects.filter(is_active=True, cafe=cafe)
    if not qs.exists():
        qs = CouponOffer.objects.filter(is_active=True, cafe__isnull=True)

    if not qs.exists():
        return None

    return qs.order_by('?').first()


@transaction.atomic
def get_or_create_week(user):
    ws = week_start_for()
    drop_week, created = DropWeek.objects.get_or_create(user=user, week_start=ws)

    if created or drop_week.options.count() == 0:
        generate_options(drop_week)

    return drop_week


def generate_options(drop_week: DropWeek):
    user = drop_week.user

    visited_ids = set(
        Order.objects.filter(user=user, cafe__isnull=False)
        .values_list('cafe_id', flat=True)
        .distinct()
    )

    new_list = list(Cafe.objects.exclude(id__in=visited_ids))
    any_list = list(Cafe.objects.all())

    chosen_cafes: list[Cafe] = []

    random.shuffle(new_list)
    random.shuffle(any_list)

    for c in new_list[:2]:
        chosen_cafes.append(c)

    for c in any_list:
        if len(chosen_cafes) >= 3:
            break
        if c not in chosen_cafes:
            chosen_cafes.append(c)

    if len(chosen_cafes) < 3:
        return

    DropOption.objects.filter(drop_week=drop_week).delete()

    for cafe in chosen_cafes[:3]:
        rarity = pick_rarity()
        offer = pick_reward_offer(cafe, rarity)
        DropOption.objects.create(
            drop_week=drop_week,
            cafe=cafe,
            rarity=rarity,
            reward_offer=offer,
        )


@transaction.atomic
def choose_option(drop_week: DropWeek, option_id: int) -> DropWeek:
    option = drop_week.options.get(id=option_id)
    drop_week.chosen_option = option
    drop_week.status = DropWeek.Status.ACTIVE
    drop_week.save(update_fields=['chosen_option', 'status'])
    return drop_week


@transaction.atomic
def try_complete_by_order(order: Order) -> bool:
    """
    Завершаем Drop после заказа:
    - нужен начисленный кэшбек (points_accrued=True)
    - нужен выбранный cafe
    - cafe заказа должен совпасть с выбранным cafe Drop
    - награда (PromoCode) не должна нарушать uniq constraint (profile, source_offer)
      -> если такой купон уже есть, просто завершаем Drop без создания нового
    """
    if not order.points_accrued:
        return False
    if not order.cafe_id:
        return False

    drop_week = (
        DropWeek.objects.filter(
            user=order.user,
            week_start=week_start_for(),
            status=DropWeek.Status.ACTIVE,
        )
        .select_related('chosen_option', 'chosen_option__cafe', 'chosen_option__reward_offer')
        .first()
    )

    if not drop_week or not drop_week.chosen_option:
        return False

    if drop_week.chosen_option.cafe_id != order.cafe_id:
        return False

    profile = Profile.objects.get(user=order.user)
    offer = drop_week.chosen_option.reward_offer

    if offer is not None and PromoCode.objects.filter(profile=profile, source_offer=offer).exists():
        drop_week.status = DropWeek.Status.COMPLETED
        drop_week.save(update_fields=['status'])
        return True

    expires_at = None
    if offer and getattr(offer, 'expires_in_days', None):
        expires_at = timezone.localdate() + timezone.timedelta(days=offer.expires_in_days)

    PromoCode.objects.create(
        profile=profile,
        code=f'DROP-{order.id}-{timezone.now().strftime("%H%M%S")}',
        description=f'Drop-награда за посещение {order.cafe.name}',
        source_offer=offer,
        expires_at=expires_at,
        status=PromoCode.Status.ACTIVE,
    )

    drop_week.status = DropWeek.Status.COMPLETED
    drop_week.save(update_fields=['status'])
    return True
