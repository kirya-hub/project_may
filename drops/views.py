from __future__ import annotations

import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from promo.services import get_active_drop_coupon
from user_profile.models import Profile

from .models import DropOption, DropWeek
from .services import choose_option, ensure_week_options

logger = logging.getLogger(__name__)

@login_required
def drops_page(request):
    if request.GET.get('refresh') == '1':
        ensure_week_options(request.user)
        return redirect('drops:drops_page')

    week = ensure_week_options(request.user)

    options = (
        DropOption.objects.filter(drop_week=week)
        .select_related('cafe', 'reward_offer')
        .order_by('id')
    )

    earned_coupon = None
    if week.status in (DropWeek.Status.ACTIVE, DropWeek.Status.COMPLETED):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        earned_coupon = get_active_drop_coupon(profile)

    return render(
        request,
        'drops/drops_page.html',
        {
            'drop_week': week,
            'options': options,
            'earned_coupon': earned_coupon,
            'show_back': True,
            'header_back_url': reverse('home'),
        },
    )

@require_POST
@login_required
def choose_drop(request, option_id: int):
    week = ensure_week_options(request.user)

    if week.status != DropWeek.Status.CHOOSING:
        logger.info(
            "choose_drop: неверный статус %s для user=%s, week=%s",
            week.status,
            request.user.pk,
            week.pk,
        )
        return redirect('drops:drops_page')

    try:
        choose_option(request.user, option_id)
    except DropOption.DoesNotExist:
        logger.warning(
            "choose_drop: option_id=%s не найден или не принадлежит week=%s, user=%s",
            option_id,
            week.pk,
            request.user.pk,
        )
        return redirect('drops:drops_page')

    logger.debug("user=%s выбрал drop option=%s", request.user.pk, option_id)
    return redirect('drops:drops_page')
