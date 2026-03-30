from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from add_order.models import Order
from feed.models import Comment, Like
from friends.models import Follow
from friends.services import friends_qs

from .forms import ProfileEditForm
from .levels import xp_needed_for_level
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
    back_url = request.GET.get('next', '').strip()

    today = timezone.localdate()
    # Купоны с кодами видит только сам владелец
    if request.user.is_authenticated and request.user == user:
        promocodes = (
            profile.promocodes.filter(status=PromoCode.Status.ACTIVE)
            .filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=today))
            .select_related('source_offer', 'source_offer__cafe')[:3]
        )
    else:
        promocodes = PromoCode.objects.none()

    friends_count = friends_qs(user).count()

    friends_preview = []
    if request.user.is_authenticated and request.user == user:
        friends_preview = friends_qs(request.user).select_related('profile')[:3]

    is_following = False
    is_friend = False

    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
        is_follower = Follow.objects.filter(follower=user, following=request.user).exists()
        is_friend = is_following and is_follower

    can_trade = request.user.is_authenticated and request.user != user and is_friend

    posts = (
        Order.objects.filter(user=user)
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

    context = {
        'profile': profile,
        'promocodes': promocodes,
        'friends_count': friends_count,
        'friends_preview': friends_preview,
        'is_following': is_following,
        'is_friend': is_friend,
        'can_trade': can_trade,
        'posts': posts,
        'show_back': bool(back_url) or (request.user.is_authenticated and request.user != user),
        'header_back_url': back_url or (reverse('home') if (request.user.is_authenticated and request.user != user) else None),
        'level': level,
        'xp': xp,
        'xp_needed': xp_needed,
        'xp_in_level': xp,
        'level_progress_percent': level_progress_percent,
        'next_level': level + 1,
    }

    return render(request, 'user_profile/profile_detail.html', context)


def profile_home(request):
    if request.user.is_authenticated:
        return redirect('my_profile')
    return render(request, 'user_profile/profile_guest.html')


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
