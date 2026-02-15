from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from user_profile.models import Profile, PromoCode

from .models import CouponOffer, PointsTransaction
from .services import NotEnoughPoints, purchase_offer


@login_required
def promo_home(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    transactions = PointsTransaction.objects.filter(user=request.user).order_by('-created_at')[:20]

    return render(
        request,
        'promo/promo_home.html',
        {
            'points': (profile.points10 or 0) / 10,
            'points10': profile.points10 or 0,
            'transactions': transactions,
        },
    )


@login_required
def coupon_shop(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    offers = (
        CouponOffer.objects.filter(is_active=True).select_related('cafe').order_by('-created_at')
    )

    owned_offer_ids = list(
        PromoCode.objects.filter(
            profile=profile,
            source_offer__isnull=False,
        ).values_list('source_offer_id', flat=True)
    )

    return render(
        request,
        'promo/coupon_shop.html',
        {
            'offers': offers,
            'points': (profile.points10 or 0) / 10,
            'points10': profile.points10 or 0,
            'owned_offer_ids': owned_offer_ids,
        },
    )


@login_required
def buy_coupon(request, offer_id: int):
    if request.method != 'POST':
        return redirect('promo:shop')

    offer = get_object_or_404(CouponOffer, id=offer_id, is_active=True)

    profile, _ = Profile.objects.get_or_create(user=request.user)

    # 🔒 Защита от повторной покупки
    already = PromoCode.objects.filter(
        profile=profile,
        source_offer=offer,
    ).first()

    if already:
        messages.info(
            request,
            f'Этот купон уже куплен. Код: {already.code}',
        )
        return redirect('promo:shop')

    try:
        new_coupon = purchase_offer(request.user, offer)
        messages.success(
            request,
            f'Купон куплен ✅ Код: {new_coupon.code}',
        )
    except NotEnoughPoints:
        messages.error(request, 'Не хватает баллов')
    except Exception:
        messages.error(
            request,
            'Не получилось купить купон. Попробуй ещё раз.',
        )

    return redirect('promo:shop')


@login_required
def my_coupons(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    today = timezone.localdate()

    # авто-обновление истёкших
    PromoCode.objects.filter(
        profile=profile,
        status='ACTIVE',
        expires_at__isnull=False,
        expires_at__lt=today,
    ).update(status='EXPIRED')

    coupons = PromoCode.objects.filter(profile=profile).order_by('-acquired_at')

    return render(
        request,
        'promo/my_coupons.html',
        {
            'coupons': coupons,
            'today': today,
        },
    )


@login_required
def use_coupon(request, coupon_id: int):
    if request.method != 'POST':
        return redirect('promo:my_coupons')

    profile, _ = Profile.objects.get_or_create(user=request.user)

    coupon = get_object_or_404(
        PromoCode,
        id=coupon_id,
        profile=profile,
    )

    if coupon.status != 'ACTIVE':
        messages.error(request, 'Этот купон нельзя использовать.')
        return redirect('promo:my_coupons')

    if coupon.expires_at and coupon.expires_at < timezone.localdate():
        coupon.status = 'EXPIRED'
        coupon.save(update_fields=['status'])
        messages.error(request, 'Купон уже истёк')
        return redirect('promo:my_coupons')

    coupon.status = 'USED'
    coupon.used_at = timezone.now()
    coupon.save(update_fields=['status', 'used_at'])

    messages.success(request, 'Купон отмечен как использованный ✅')
    return redirect('promo:my_coupons')
