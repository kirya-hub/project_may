from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone

from cafes.models import CafeStaff
from user_profile.models import PromoCode


def _cafe_staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        if not (request.user.is_staff or CafeStaff.objects.filter(user=request.user).exists()):
            return HttpResponseForbidden('Доступ запрещён. Нужна учётная запись сотрудника кафе.')
        return view_func(request, *args, **kwargs)

    return wrapper


@_cafe_staff_required
def staff_redeem(request):
    result = None
    error = None

    if request.method == 'POST':
        code = (request.POST.get('code') or '').strip().upper()
        if not code:
            error = 'Введите код активации.'
        else:
            try:
                promo = PromoCode.objects.select_related(
                    'profile__user', 'source_offer', 'source_offer__cafe'
                ).get(activation_code=code, status=PromoCode.Status.ACTIVE)

                today = timezone.localdate()
                if promo.expires_at and promo.expires_at < today:
                    # Обновляем статус в БД — expire_profile_coupons мог не успеть
                    promo.status = PromoCode.Status.EXPIRED
                    promo.save(update_fields=['status'])
                    error = 'Купон истёк.'
                else:
                    promo.status = PromoCode.Status.USED
                    promo.used_at = timezone.now()
                    promo.save(update_fields=['status', 'used_at'])
                    result = promo

            except PromoCode.DoesNotExist:
                error = 'Купон не найден или уже использован.'

    return render(request, 'staff/redeem.html', {'result': result, 'error': error})
