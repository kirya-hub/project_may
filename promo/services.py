import secrets
import string
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from user_profile.models import Profile, PromoCode

from .models import CouponOffer, PointsTransaction

PERCENT = Decimal('0.05')
DAILY_LIMIT = 2


def _to_points10(total_sum: Decimal) -> int:
    raw = total_sum * PERCENT * Decimal('10')
    return int(raw.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


@transaction.atomic
def accrue_points_for_order(order) -> int:
    if order.points_accrued:
        return 0

    if order.total_sum is None:
        return 0

    today = timezone.localdate()

    today_count = PointsTransaction.objects.filter(
        user=order.user,
        kind=PointsTransaction.Kind.ACCRUAL,
        created_at__date=today,
    ).count()

    if today_count >= DAILY_LIMIT:
        return 0

    points10 = _to_points10(order.total_sum)
    if points10 <= 0:
        return 0

    profile, _ = Profile.objects.get_or_create(user=order.user)
    profile.points10 = (profile.points10 or 0) + points10
    profile.save(update_fields=['points10'])

    PointsTransaction.objects.create(
        user=order.user,
        order=order,
        amount10=points10,
        kind=PointsTransaction.Kind.ACCRUAL,
    )

    order.points_accrued = True
    order.save(update_fields=['points_accrued'])

    return points10


class NotEnoughPoints(Exception):
    pass


def generate_code(groups: int = 2, group_len: int = 4) -> str:
    """
    Пример: ABCD-7K2P
    """
    alphabet = string.ascii_uppercase + string.digits
    parts = []
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
    if not offer.is_active:
        raise ValueError('Купон не продаётся')

    profile, _ = Profile.objects.select_for_update().get_or_create(user=user)

    existing = PromoCode.objects.filter(profile=profile, source_offer=offer).first()
    if existing:
        return existing

    cost = int(offer.cost_points10 or 0)
    if (profile.points10 or 0) < cost:
        raise NotEnoughPoints

    # списали баллы
    profile.points10 = (profile.points10 or 0) - cost
    profile.save(update_fields=['points10'])

    PointsTransaction.objects.create(
        user=user,
        order=None,
        amount10=-cost,
        kind=PointsTransaction.Kind.SPEND,
    )

    expires_at = None
    if offer.expires_in_days:
        expires_at = timezone.localdate() + timedelta(days=int(offer.expires_in_days))

    code = generate_unique_code()

    return PromoCode.objects.create(
        profile=profile,
        source_offer=offer,
        code=code,
        description=offer.description,
        expires_at=expires_at,
        status='ACTIVE',
    )
