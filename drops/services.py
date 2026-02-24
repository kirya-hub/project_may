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

    DropWeek.objects.filter(
        user=user,
        week_start__lt=ws,
        status__in=[DropWeek.Status.CHOOSING, DropWeek.Status.ACTIVE],
    ).update(status=DropWeek.Status.EXPIRED)

    drop_week, created = DropWeek.objects.get_or_create(user=user, week_start=ws)

    if created or drop_week.options.count() == 0:
        generate_options(drop_week)

    if (
        drop_week.status in [DropWeek.Status.CHOOSING, DropWeek.Status.ACTIVE]
        and drop_week.seconds_left <= 0
    ):
        drop_week.status = DropWeek.Status.EXPIRED
        drop_week.save(update_fields=['status'])

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

    random.shuffle(new_list)
    random.shuffle(any_list)

    if len(new_list) >= 3:
        target_new = 3
    elif len(new_list) >= 2:
        target_new = 2
    else:
        target_new = len(new_list)

    chosen_cafes: list[Cafe] = []
    chosen_cafes.extend(new_list[:target_new])

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

    try:
        from feed.models import FeedEvent

        FeedEvent.objects.create(
            user=drop_week.user,
            kind=FeedEvent.Kind.DROP_CHOSEN,
            cafe=option.cafe,
            text=f'выбрал Drop в {option.cafe.name}',
        )
    except Exception:
        pass

    return drop_week


@transaction.atomic
def try_complete_by_order(order: Order) -> bool:
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
