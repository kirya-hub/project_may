from __future__ import annotations

import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from promo.services import get_active_drop_coupon
from user_profile.models import Profile

from .models import DropOption, DropWeek
from .services import (
    choose_option,
    get_claimable_week,
    get_current_week,
    get_user_week_stats,
)

logger = logging.getLogger(__name__)

_TIER_TABLE = {
    'BRONZE': {
        'levels': [
            {'range': '1–6',   'COMMON': 85, 'RARE': 15, 'LEGENDARY': None},
            {'range': '7–12',  'COMMON': 75, 'RARE': 25, 'LEGENDARY': None},
            {'range': '13–15', 'COMMON': 65, 'RARE': 35, 'LEGENDARY': None},
        ],
    },
    'GOLD': {
        'levels': [
            {'range': '1–6',   'COMMON': 65, 'RARE': 25, 'LEGENDARY': 10},
            {'range': '7–12',  'COMMON': 50, 'RARE': 35, 'LEGENDARY': 15},
            {'range': '13–15', 'COMMON': 35, 'RARE': 40, 'LEGENDARY': 25},
        ],
    },
}

_LEVEL_BONUSES = [
    {'range': '1–3',  'bonus': 0},
    {'range': '4–6',  'bonus': 5},
    {'range': '7–9',  'bonus': 10},
    {'range': '10–12','bonus': 15},
    {'range': '13–14','bonus': 18},
    {'range': '15',   'bonus': 25},
]


@login_required
def drops_page(request):
    user = request.user
    current_week = get_current_week(user)
    claimable_week = get_claimable_week(user)
    tier, adjusted_sum = get_user_week_stats(user)

    earned_coupon = None
    if claimable_week and claimable_week.status == DropWeek.Status.COMPLETED:
        profile, _ = Profile.objects.get_or_create(user=user)
        earned_coupon = get_active_drop_coupon(profile)

    cta_active = bool(tier) or bool(
        claimable_week and claimable_week.status == DropWeek.Status.CHOOSING
    )

    return render(
        request,
        'drops/drops_page.html',
        {
            'current_week': current_week,
            'claimable_week': claimable_week,
            'tier': tier,
            'adjusted_sum': adjusted_sum,
            'earned_coupon': earned_coupon,
            'cta_active': cta_active,
            'tier_table': _TIER_TABLE,
            'level_bonuses': _LEVEL_BONUSES,
            'show_back': True,
            'header_back_url': reverse('home'),
        },
    )


@login_required
def grab(request):
    user = request.user
    current_week = get_current_week(user)
    claimable_week = get_claimable_week(user)
    tier, _ = get_user_week_stats(user)

    profile, _ = Profile.objects.get_or_create(user=user)
    earned_coupon = None
    options = []
    state = 'no_tier'

    if claimable_week:
        if claimable_week.status == DropWeek.Status.COMPLETED:
            state = 'completed'
            earned_coupon = get_active_drop_coupon(profile)
        elif claimable_week.status == DropWeek.Status.CHOOSING:
            state = 'claimable'
            options = list(
                DropOption.objects.filter(drop_week=claimable_week)
                .select_related('cafe', 'reward_offer')
                .order_by('id')
            )
    elif tier:
        state = 'wait'

    return render(
        request,
        'drops/grab.html',
        {
            'state': state,
            'current_week': current_week,
            'claimable_week': claimable_week,
            'options': options,
            'earned_coupon': earned_coupon,
            'show_back': True,
            'header_back_url': reverse('drops:drops_page'),
        },
    )


def drops_info(request):
    return render(request, 'drops/info.html', {
        'tier_table': _TIER_TABLE,
        'level_bonuses': _LEVEL_BONUSES,
        'show_back': True,
        'header_back_url': reverse('drops:drops_page'),
    })


@require_POST
@login_required
def choose_drop(request, option_id: int):
    claimable_week = get_claimable_week(request.user)

    if not claimable_week or claimable_week.status != DropWeek.Status.CHOOSING:
        logger.info(
            'choose_drop: нет доступного дропа для user=%s',
            request.user.pk,
        )
        return redirect('drops:grab')

    try:
        choose_option(request.user, option_id)
    except DropOption.DoesNotExist:
        logger.warning(
            'choose_drop: option_id=%s не найден для user=%s',
            option_id,
            request.user.pk,
        )
        return redirect('drops:grab')

    logger.debug('user=%s выбрал drop option=%s', request.user.pk, option_id)
    return redirect('drops:grab')
