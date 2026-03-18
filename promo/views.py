from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from user_profile.models import Profile, PromoCode

from .models import CouponOffer, PointsTransaction
from .services import (
    ActiveShopCouponExists,
    NotEnoughPoints,
    expire_profile_coupons,
    get_active_drop_coupon,
    get_active_shop_coupon,
    get_rotating_shop_offers,
    purchase_offer,
)


def _get_points_context(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


@login_required
def promo_home(request):
    profile = _get_points_context(request.user)
    expire_profile_coupons(profile)
    transactions = (
        PointsTransaction.objects.filter(user=request.user)
        .select_related('order')
        .order_by('-created_at')[:20]
    )

    return render(
        request,
        'promo/promo_home.html',
        {
            'points': profile.points,
            'points10': profile.points10 or 0,
            'transactions': transactions,
        },
    )


@login_required
def coupon_shop(request):
    profile = _get_points_context(request.user)
    expire_profile_coupons(profile)

    offers = get_rotating_shop_offers()
    active_shop_coupon = get_active_shop_coupon(profile)
    active_drop_coupon = get_active_drop_coupon(profile)

    return render(
        request,
        'promo/coupon_shop.html',
        {
            'offers': offers,
            'points': profile.points,
            'points10': profile.points10 or 0,
            'active_shop_coupon': active_shop_coupon,
            'active_drop_coupon': active_drop_coupon,
            'show_back': True,
            'header_back_url': reverse('promo:home'),
        },
    )


@login_required
def buy_coupon(request, offer_id: int):
    if request.method != 'POST':
        return redirect('promo:shop')

    offer = get_object_or_404(CouponOffer, id=offer_id, is_active=True, available_in_shop=True)

    try:
        new_coupon = purchase_offer(request.user, offer)
        messages.success(request, f'Купон куплен ✅ Код: {new_coupon.code}')
    except ActiveShopCouponExists:
        messages.error(
            request,
            'Сначала используй или дождись окончания текущего магазинного купона.',
        )
    except NotEnoughPoints:
        messages.error(request, 'Не хватает баллов')
    except Exception:
        messages.error(request, 'Не получилось купить купон. Попробуй ещё раз.')

    return redirect('promo:shop')


@login_required
def my_coupons(request):
    profile = _get_points_context(request.user)
    expire_profile_coupons(profile)

    status = (request.GET.get('status') or 'ACTIVE').upper()
    allowed = {PromoCode.Status.ACTIVE, PromoCode.Status.USED, PromoCode.Status.EXPIRED}
    if status not in allowed:
        status = PromoCode.Status.ACTIVE

    coupons_qs = PromoCode.objects.filter(profile=profile).select_related(
        'source_offer', 'source_offer__cafe'
    )

    counts = {
        'ACTIVE': coupons_qs.filter(status=PromoCode.Status.ACTIVE).count(),
        'USED': coupons_qs.filter(status=PromoCode.Status.USED).count(),
        'EXPIRED': coupons_qs.filter(status=PromoCode.Status.EXPIRED).count(),
    }

    coupons = coupons_qs.filter(status=status).order_by('-acquired_at')

    return render(
        request,
        'promo/my_coupons.html',
        {
            'coupons': coupons,
            'active_tab': status,
            'counts': counts,
            'show_back': True,
            'header_back_url': reverse('promo:home'),
        },
    )


@login_required
def use_coupon(request, coupon_id: int):
    if request.method != 'POST':
        return redirect('promo:my_coupons')

    profile = _get_points_context(request.user)
    coupon = get_object_or_404(PromoCode, id=coupon_id, profile=profile)

    if coupon.status != PromoCode.Status.ACTIVE:
        messages.error(request, 'Этот купон нельзя использовать.')
        return redirect('promo:my_coupons')

    if coupon.expires_at and coupon.expires_at < timezone.localdate():
        coupon.status = PromoCode.Status.EXPIRED
        coupon.save(update_fields=['status'])
        messages.error(request, 'Купон уже истёк')
        return redirect('promo:my_coupons')

    coupon.status = PromoCode.Status.USED
    coupon.used_at = timezone.now()
    coupon.save(update_fields=['status', 'used_at'])

    messages.success(request, 'Купон отмечен как использованный ✅')
    return redirect('promo:my_coupons')
