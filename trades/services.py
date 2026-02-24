from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from friends.services import friends_qs
from user_profile.models import Profile, PromoCode

from .models import TradeActivity, TradeItem, TradeOffer


class TradeError(Exception):
    pass


class NotFriends(TradeError):
    pass


class InvalidRatio(TradeError):
    pass


class CouponNotAvailable(TradeError):
    pass


def _check_ratio(offered_count: int, requested_count: int) -> None:
    ok = (
        offered_count == requested_count
        or offered_count == 2 * requested_count
        or requested_count == 2 * offered_count
    )
    if not ok:
        raise InvalidRatio('Разрешён обмен 1↔1 или 2↔1')


def _ensure_friends(from_user, to_user) -> None:
    if not friends_qs(from_user).filter(id=to_user.id).exists():
        raise NotFriends('Обмен доступен только между друзьями (взаимная подписка)')


def _ensure_coupons_active_and_owned(user, coupon_ids):
    today = timezone.localdate()
    qs = PromoCode.objects.select_related('profile', 'profile__user').filter(id__in=coupon_ids)
    coupons = list(qs)

    if len(coupons) != len(set(coupon_ids)):
        raise CouponNotAvailable('Часть купонов не найдена')

    for c in coupons:
        if c.profile.user_id != user.id:
            raise CouponNotAvailable('Купон не принадлежит пользователю')
        if c.status != PromoCode.Status.ACTIVE:
            raise CouponNotAvailable('Можно обменивать только активные купоны')
        if c.expires_at and c.expires_at < today:
            raise CouponNotAvailable('Нельзя обменять истёкший купон')

    busy = TradeItem.objects.filter(
        promocode_id__in=coupon_ids,
        trade__status=TradeOffer.Status.PENDING,
    ).exists()
    if busy:
        raise CouponNotAvailable('Один из купонов уже участвует в другом предложении')

    return coupons


def _check_no_same_type_inside_one_side(coupons: list[PromoCode], side_label: str) -> None:
    seen: set[tuple[str, object]] = set()
    for c in coupons:
        key: tuple[str, object]
        if c.source_offer_id is not None:
            key = ('offer', c.source_offer_id)
        else:
            key = ('code', c.code)

        if key in seen:
            raise CouponNotAvailable(f'Нельзя выбрать два одинаковых купона в блоке «{side_label}»')
        seen.add(key)


@transaction.atomic
def create_trade_offer(
    from_user, to_user, offered_ids, requested_ids, message: str = ''
) -> TradeOffer:
    _ensure_friends(from_user, to_user)

    offered_ids = [int(x) for x in offered_ids]
    requested_ids = [int(x) for x in requested_ids]

    if not offered_ids or not requested_ids:
        raise TradeError('Нужно выбрать купоны с обеих сторон')

    _check_ratio(len(offered_ids), len(requested_ids))

    offered = _ensure_coupons_active_and_owned(from_user, offered_ids)
    requested = _ensure_coupons_active_and_owned(to_user, requested_ids)

    _check_no_same_type_inside_one_side(offered, 'Я отдаю')
    _check_no_same_type_inside_one_side(requested, 'Я хочу')

    trade = TradeOffer.objects.create(
        from_user=from_user,
        to_user=to_user,
        message=(message or '').strip(),
        status=TradeOffer.Status.PENDING,
    )

    TradeItem.objects.bulk_create(
        [TradeItem(trade=trade, promocode=c, side=TradeItem.Side.OFFERED) for c in offered]
        + [TradeItem(trade=trade, promocode=c, side=TradeItem.Side.REQUESTED) for c in requested]
    )

    TradeActivity.objects.create(kind=TradeActivity.Kind.CREATED, actor=from_user, trade=trade)
    return trade


@transaction.atomic
def accept_trade(user, trade: TradeOffer) -> TradeOffer:
    trade = TradeOffer.objects.select_for_update().get(pk=trade.pk)

    if trade.status != TradeOffer.Status.PENDING:
        raise TradeError('Предложение уже обработано')
    if user.id != trade.to_user_id:
        raise TradeError('Принять может только получатель предложения')

    items = (
        TradeItem.objects.select_related('promocode', 'promocode__profile')
        .select_for_update()
        .filter(trade=trade)
    )
    offered = [i.promocode for i in items if i.side == TradeItem.Side.OFFERED]
    requested = [i.promocode for i in items if i.side == TradeItem.Side.REQUESTED]

    today = timezone.localdate()
    for c in offered + requested:
        if c.status != PromoCode.Status.ACTIVE:
            raise CouponNotAvailable('Один из купонов стал неактивным')
        if c.expires_at and c.expires_at < today:
            raise CouponNotAvailable('Один из купонов истёк')

    if any(c.profile.user_id != trade.from_user_id for c in offered):
        raise CouponNotAvailable('Купон у отправителя уже изменился')
    if any(c.profile.user_id != trade.to_user_id for c in requested):
        raise CouponNotAvailable('Купон у получателя уже изменился')

    _check_no_same_type_inside_one_side(offered, 'Я отдаю')
    _check_no_same_type_inside_one_side(requested, 'Я хочу')

    from_profile, _ = Profile.objects.select_for_update().get_or_create(user=trade.from_user)
    to_profile, _ = Profile.objects.select_for_update().get_or_create(user=trade.to_user)

    PromoCode.objects.filter(id__in=[c.id for c in requested]).update(profile=from_profile)
    PromoCode.objects.filter(id__in=[c.id for c in offered]).update(profile=to_profile)

    trade.status = TradeOffer.Status.ACCEPTED
    trade.responded_at = timezone.now()
    trade.save(update_fields=['status', 'responded_at'])

    TradeActivity.objects.create(kind=TradeActivity.Kind.ACCEPTED, actor=user, trade=trade)
    return trade


@transaction.atomic
def decline_trade(user, trade: TradeOffer) -> TradeOffer:
    trade = TradeOffer.objects.select_for_update().get(pk=trade.pk)

    if trade.status != TradeOffer.Status.PENDING:
        raise TradeError('Предложение уже обработано')
    if user.id != trade.to_user_id:
        raise TradeError('Отклонить может только получатель предложения')

    trade.status = TradeOffer.Status.DECLINED
    trade.responded_at = timezone.now()
    trade.save(update_fields=['status', 'responded_at'])

    TradeActivity.objects.create(kind=TradeActivity.Kind.DECLINED, actor=user, trade=trade)
    return trade


@transaction.atomic
def cancel_trade(user, trade: TradeOffer) -> TradeOffer:
    trade = TradeOffer.objects.select_for_update().get(pk=trade.pk)

    if trade.status != TradeOffer.Status.PENDING:
        raise TradeError('Отменить можно только ожидающее предложение')
    if user.id != trade.from_user_id:
        raise TradeError('Отменить может только отправитель предложения')

    trade.status = TradeOffer.Status.CANCELLED
    trade.responded_at = timezone.now()
    trade.save(update_fields=['status', 'responded_at'])

    TradeActivity.objects.create(kind=TradeActivity.Kind.CANCELLED, actor=user, trade=trade)
    return trade
