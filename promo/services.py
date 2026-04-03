from __future__ import annotations

import hashlib
import logging
import secrets
import string
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from add_order.models import Order as OrderModel
from user_profile.levels import add_xp
from user_profile.models import Profile, PromoCode

from .models import CouponOffer, PointsTransaction, TransactionKind

logger = logging.getLogger(__name__)

BASE_CASHBACK_PERCENT = Decimal('0.10')
DAILY_ACCRUAL_LIMIT = 2
MIN_TOTAL_SUM = Decimal('1.00')
MAX_POINTS10_PER_ORDER = 5000
SHOP_REFRESH_HOURS = 72

class NotEnoughPoints(Exception):
    pass

class ActiveShopCouponExists(Exception):
    pass

def _cashback_percent_for_profile(profile: Profile | None) -> Decimal:
    level = int(getattr(profile, 'level', 1) or 1) if profile else 1
    if level >= 10:
        return Decimal('0.15')
    if level >= 5:
        return Decimal('0.12')
    return BASE_CASHBACK_PERCENT

def _to_points10(total_sum: Decimal, percent: Decimal) -> int:
    raw = total_sum * percent * Decimal('10')
    points10 = int(raw.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    return max(0, min(points10, MAX_POINTS10_PER_ORDER))

def _get_or_create_profile(user) -> Profile:
    return Profile.objects.select_for_update().get_or_create(user=user)[0]

def _active_coupon_q(profile: Profile):
    today = timezone.localdate()
    return Q(profile=profile, status=PromoCode.Status.ACTIVE) & (
        Q(expires_at__isnull=True) | Q(expires_at__gte=today)
    )

def expire_profile_coupons(profile: Profile, *, origin: str | None = None) -> int:
    qs = PromoCode.objects.filter(
        profile=profile,
        status=PromoCode.Status.ACTIVE,
        expires_at__lt=timezone.localdate(),
    )
    if origin:
        qs = qs.filter(origin=origin)
    return qs.update(status=PromoCode.Status.EXPIRED)

def get_active_coupons(profile: Profile, *, origin: str | None = None):
    expire_profile_coupons(profile, origin=origin)
    qs = PromoCode.objects.filter(_active_coupon_q(profile)).select_related(
        'source_offer', 'source_offer__cafe'
    )
    if origin:
        qs = qs.filter(origin=origin)
    return qs.order_by('-acquired_at')

def get_active_shop_coupon(profile: Profile):
    return get_active_coupons(profile, origin=PromoCode.Origin.SHOP).first()

def get_active_drop_coupon(profile: Profile):
    return get_active_coupons(profile, origin=PromoCode.Origin.DROP).first()

def _current_shop_window_key(now=None) -> str:
    now = now or timezone.now()
    hours = int(now.timestamp() // (SHOP_REFRESH_HOURS * 3600))
    return str(hours)

def _pick_deterministic_offer(qs, seed_key: str) -> CouponOffer | None:
    offers = list(qs.order_by('id')[:200])
    if not offers:
        return None
    if len(offers) == 1:
        return offers[0]
    digest = hashlib.sha256(seed_key.encode('utf-8')).hexdigest()
    index = int(digest[:12], 16) % len(offers)
    return offers[index]

def get_rotating_shop_offers(now=None) -> list[CouponOffer]:
    seed = _current_shop_window_key(now=now)
    base_qs = CouponOffer.objects.filter(is_active=True, available_in_shop=True)
    slots = [
        (
            'coffee',
            base_qs.filter(
                reward_type=CouponOffer.RewardType.COFFEE,
                rarity=CouponOffer.Rarity.COMMON,
            ),
        ),
        (
            'dessert',
            base_qs.filter(
                reward_type=CouponOffer.RewardType.DESSERT,
                rarity=CouponOffer.Rarity.COMMON,
            ),
        ),
        (
            'discount',
            base_qs.filter(
                reward_type=CouponOffer.RewardType.DISCOUNT,
                rarity=CouponOffer.Rarity.COMMON,
            ),
        ),
        (
            'rare',
            base_qs.filter(
                reward_type=CouponOffer.RewardType.DISCOUNT,
                rarity=CouponOffer.Rarity.RARE,
            ),
        ),
    ]

    offers: list[CouponOffer] = []
    seen_ids: set[int] = set()
    for slot_name, qs in slots:
        offer = _pick_deterministic_offer(qs.exclude(id__in=seen_ids), f'{seed}:{slot_name}')
        if offer is None:
            offer = _pick_deterministic_offer(qs, f'{seed}:{slot_name}:fallback')
        if offer is not None and offer.id not in seen_ids:
            offers.append(offer)
            seen_ids.add(offer.id)
    return offers

@transaction.atomic
def accrue_points_for_order(order) -> int:

    order = OrderModel.objects.select_for_update().get(pk=order.pk)

    if order.points_accrued:
        return 0

    if getattr(order, 'is_duplicate', False):
        return 0

    if order.total_sum is None:
        return 0

    total_sum = Decimal(str(order.total_sum))
    if total_sum < MIN_TOTAL_SUM:
        return 0

    today = timezone.localdate()

    today_count = (
        PointsTransaction.objects.filter(
            user=order.user,
            kind=TransactionKind.ACCRUAL,
            created_at__date=today,
        )
        .count()
    )
    if today_count >= DAILY_ACCRUAL_LIMIT:
        logger.debug(
            "accrue_points: лимит дня достигнут для user=%s (count=%d)",
            order.user_id,
            today_count,
        )
        return 0

    profile = _get_or_create_profile(order.user)

    percent = _cashback_percent_for_profile(profile)
    points10 = _to_points10(total_sum, percent)
    if points10 <= 0:
        return 0

    try:
        PointsTransaction.objects.create(
            user=order.user,
            order=order,
            amount10=points10,
            kind=TransactionKind.ACCRUAL,
        )
    except IntegrityError:

        logger.warning(
            "accrue_points: IntegrityError (дубль транзакции) для order=%s", order.pk
        )
        order.points_accrued = True
        order.save(update_fields=['points_accrued'])
        return 0

    profile.points10 = (profile.points10 or 0) + points10
    profile.save(update_fields=['points10'])

    order.points_accrued = True
    order.save(update_fields=['points_accrued'])

    logger.debug(
        "accrue_points: начислено %d (x10) для user=%s, order=%s",
        points10,
        order.user_id,
        order.pk,
    )

    try:
        add_xp(order.user, 10)
    except Exception as exc:
        logger.warning("add_xp не удался для user=%s: %s", order.user_id, exc)

    return points10

def generate_code(groups: int = 2, group_len: int = 4) -> str:
    alphabet = string.ascii_uppercase + string.digits
    parts: list[str] = []
    for _ in range(groups):
        parts.append(''.join(secrets.choice(alphabet) for _ in range(group_len)))
    return '-'.join(parts)

def generate_unique_code(max_attempts: int = 10) -> str:
    for _ in range(max_attempts):
        code = generate_code()
        if not PromoCode.objects.filter(code=code).exists():
            return code
    return generate_code(groups=3, group_len=4)

@transaction.atomic
def purchase_offer(user, offer: CouponOffer) -> PromoCode:
    if not offer.is_active or not offer.available_in_shop:
        raise ValueError('Купон не продаётся')

    profile = _get_or_create_profile(user)

    active_shop_coupon = get_active_shop_coupon(profile)
    if active_shop_coupon is not None:
        raise ActiveShopCouponExists

    cost = int(offer.cost_points10 or 0)
    if (profile.points10 or 0) < cost:
        raise NotEnoughPoints

    profile.points10 = (profile.points10 or 0) - cost
    profile.save(update_fields=['points10'])

    PointsTransaction.objects.create(
        user=user,
        order=None,
        amount10=-cost,
        kind=TransactionKind.SPEND,
    )

    expires_at = None
    if offer.expires_in_days:
        expires_at = timezone.localdate() + timedelta(days=int(offer.expires_in_days))

    code = generate_unique_code()

    logger.debug(
        "purchase_offer: user=%s купил offer=%s за %d points10",
        user.pk,
        offer.pk,
        cost,
    )

    return PromoCode.objects.create(
        profile=profile,
        source_offer=offer,
        origin=PromoCode.Origin.SHOP,
        code=code,
        description=offer.description,
        expires_at=expires_at,
        status=PromoCode.Status.ACTIVE,
    )
