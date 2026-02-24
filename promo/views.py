from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from user_profile.models import Profile, PromoCode

from .models import CouponOffer, PointsBalance, PointsTransaction
from .services import NotEnoughPoints, purchase_offer


def _get_points_context(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    balance, _ = PointsBalance.objects.get_or_create(user=user)

    if (balance.points10 or 0) == 0 and (profile.points10 or 0) > 0:
        balance.points10 = profile.points10 or 0
        balance.save(update_fields=['points10', 'updated_at'])

    return profile, balance


@login_required
def promo_home(request):
    profile, balance = _get_points_context(request.user)
    transactions = (
        PointsTransaction.objects.filter(user=request.user)
        .select_related('order')
        .order_by('-created_at')[:20]
    )

    return render(
        request,
        'promo/promo_home.html',
        {
            'points': (balance.points10 or 0) / 10,
            'points10': balance.points10 or 0,
            'transactions': transactions,
        },
    )


@login_required
def coupon_shop(request):
    profile, balance = _get_points_context(request.user)

    offers = (
        CouponOffer.objects.filter(is_active=True).select_related('cafe').order_by('-created_at')
    )

    owned_offer_ids = list(
        PromoCode.objects.filter(profile=profile, source_offer__isnull=False).values_list(
            'source_offer_id', flat=True
        )
    )

    return render(
        request,
        'promo/coupon_shop.html',
        {
            'offers': offers,
            'points': (balance.points10 or 0) / 10,
            'points10': balance.points10 or 0,
            'owned_offer_ids': owned_offer_ids,
            'show_back': True,
            'header_back_url': reverse('promo:home'),
        },
    )


@login_required
def buy_coupon(request, offer_id: int):
    if request.method != 'POST':
        return redirect('promo:shop')

    offer = get_object_or_404(CouponOffer, id=offer_id, is_active=True)
    profile, _balance = _get_points_context(request.user)

    already = PromoCode.objects.filter(profile=profile, source_offer=offer).first()
    if already:
        messages.info(request, f'Этот купон уже куплен. Код: {already.code}')
        return redirect('promo:shop')

    try:
        new_coupon = purchase_offer(request.user, offer)
        messages.success(request, f'Купон куплен ✅ Код: {new_coupon.code}')
    except NotEnoughPoints:
        messages.error(request, 'Не хватает баллов')
    except Exception:
        messages.error(request, 'Не получилось купить купон. Попробуй ещё раз.')

    return redirect('promo:shop')


@login_required
def my_coupons(request):
    profile, _balance = _get_points_context(request.user)
    today = timezone.localdate()

    PromoCode.objects.filter(
        profile=profile,
        status=PromoCode.Status.ACTIVE,
        expires_at__isnull=False,
        expires_at__lt=today,
    ).update(status=PromoCode.Status.EXPIRED)

    status = (request.GET.get('status') or 'ACTIVE').upper()
    allowed = {PromoCode.Status.ACTIVE, PromoCode.Status.USED, PromoCode.Status.EXPIRED}
    if status not in allowed:
        status = PromoCode.Status.ACTIVE

    coupons_qs = PromoCode.objects.filter(profile=profile)

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

    profile, _balance = _get_points_context(request.user)

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
