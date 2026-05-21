from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from add_order.models import Order
from drops.services import _level_bonus, _rarity_weights_for_profile, get_user_tier
from feed.models import Comment, Like
from friends.models import Follow
from friends.services import friends_qs
from promo.services import _cashback_percent_for_profile

from .forms import ProfileEditForm
from .levels import xp_needed_for_level, MAX_LEVEL
from .models import Profile, PromoCode


@login_required
def my_profile(request):
    return redirect('profile_by_username', username=request.user.username)


def profile_detail(request, username=None, user_id=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = get_object_or_404(User, id=user_id)

    profile = get_object_or_404(Profile, user=user)
    is_other_user = request.user.is_authenticated and request.user != user
    back_url = request.GET.get('next', '').strip()
    if back_url and not url_has_allowed_host_and_scheme(back_url, allowed_hosts={request.get_host()}):
        back_url = ''
    if back_url.startswith('/trade/new/') or (not back_url and is_other_user):
        back_url = reverse('friends:friends_page')

    today = timezone.localdate()
    promocodes = (
        profile.promocodes.filter(status=PromoCode.Status.ACTIVE)
        .filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=today))
        .select_related('source_offer', 'source_offer__cafe', 'source_offer__menu_item')[:3]
    )

    friends_count = friends_qs(user).count()

    friends_preview = friends_qs(user).select_related('profile')[:3]

    is_following = False
    is_friend = False

    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
        is_follower = Follow.objects.filter(follower=user, following=request.user).exists()
        is_friend = is_following and is_follower

    can_trade = request.user.is_authenticated and request.user != user and is_friend

    posts = (
        Order.objects.filter(user=user, is_duplicate=False)
        .select_related('user', 'user__profile', 'cafe')
        .prefetch_related(
            Prefetch(
                'comments',
                queryset=Comment.objects.select_related('user', 'user__profile').order_by(
                    'created_at'
                ),
            )
        )
        .order_by('-created_at')
        .annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
        )
    )

    if request.user.is_authenticated:
        posts = posts.annotate(
            is_liked=Exists(Like.objects.filter(user=request.user, order=OuterRef('pk')))
        )
    else:
        posts = posts.annotate(is_liked=models.Value(False, output_field=models.BooleanField()))

    level = getattr(profile, 'level', 1) or 1
    xp = getattr(profile, 'xp', 0) or 0
    xp_needed = xp_needed_for_level(level)
    level_progress_percent = int(min(100, (xp / xp_needed) * 100)) if xp_needed > 0 else 0

    user_tier = None
    week_sum = 0
    week_sum_adjusted = 0
    tier_chances = {}

    if request.user.is_authenticated and request.user == user:
        from datetime import date, timedelta
        from django.db.models import Sum

        user_tier = get_user_tier(user)
        today = date.today()
        week_monday = today - timedelta(days=today.weekday())
        result = Order.objects.filter(
            user=user,
            created_at__date__gte=week_monday,
            is_duplicate=False,
            total_sum__gte=200,
        ).aggregate(total=Sum('total_sum'))
        week_sum = float(result['total'] or 0)
        bonus = _level_bonus(level)
        week_sum_adjusted = week_sum * (1 + bonus / 100)

        if user_tier:
            weights = _rarity_weights_for_profile(profile, user_tier)
            total_w = sum(w for _, w in weights)
            tier_chances = {r: round(w / total_w * 100) for r, w in weights}

    # Шансы при Gold тире для текущего уровня (показываем всегда)
    _gold_weights = _rarity_weights_for_profile(profile, 'GOLD')
    _gold_total = sum(w for _, w in _gold_weights)
    tier_chances_gold = {r: round(w / _gold_total * 100) for r, w in _gold_weights}

    cashback_pct = int(_cashback_percent_for_profile(profile) * 100)
    level_bonus_pct = _level_bonus(level)
    tier_label = {'GOLD': 'Gold', 'BRONZE': 'Bronze'}.get(user_tier, '') if user_tier else ''

    # Max level bonuses for the popup (level 15, GOLD tier)
    class _MaxProfile:
        level = MAX_LEVEL
    _max_weights_gold = _rarity_weights_for_profile(_MaxProfile(), 'GOLD')
    _max_total_gold = sum(w for _, w in _max_weights_gold)
    max_chances_gold = {r: round(w / _max_total_gold * 100) for r, w in _max_weights_gold}
    max_cashback_pct = 15  # level 15 >= 10 → 15%
    max_level_bonus_pct = _level_bonus(MAX_LEVEL)

    context = {
        'profile': profile,
        'promocodes': promocodes,
        'friends_count': friends_count,
        'friends_preview': friends_preview,
        'is_following': is_following,
        'is_friend': is_friend,
        'can_trade': can_trade,
        'posts': posts,
        'show_back': bool(back_url) or is_other_user,
        'header_back_url': back_url or None,
        'level': level,
        'xp': xp,
        'xp_needed': xp_needed,
        'xp_in_level': xp,
        'level_progress_percent': level_progress_percent,
        'next_level': level + 1,
        'is_own_profile': request.user.is_authenticated and request.user == user,
        'user_tier': user_tier,
        'week_sum': week_sum,
        'week_sum_adjusted': week_sum_adjusted,
        'tier_chances': tier_chances,
        'tier_chances_gold': tier_chances_gold,
        'cashback_pct': cashback_pct,
        'level_bonus_pct': level_bonus_pct,
        'tier_label': tier_label,
        'max_level': MAX_LEVEL,
        'max_cashback_pct': max_cashback_pct,
        'max_chances_gold': max_chances_gold,
        'max_level_bonus_pct': max_level_bonus_pct,
    }

    return render(request, 'user_profile/profile_detail.html', context)


@login_required
def profile_home(request):
    return redirect('my_profile')


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('my_profile')
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'user_profile/edit_profile.html', {'form': form})
