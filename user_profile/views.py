from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from add_order.models import Order
from feed.models import Like
from friends.models import Follow
from friends.services import friends_qs

from .forms import ProfileEditForm
from .models import Profile


@login_required
def my_profile(request):
    return redirect('profile_by_username', username=request.user.username)


def profile_detail(request, username=None, user_id=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = get_object_or_404(User, id=user_id)

    profile = get_object_or_404(Profile, user=user)

    today = timezone.localdate()
    promocodes = profile.promocodes.filter(status='ACTIVE').filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=today)
    )

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

    posts = (
        Order.objects.filter(user=user)
        .select_related('user', 'user__profile', 'cafe')
        .order_by('-created_at')
        .annotate(likes_count=Count('likes', distinct=True))
    )

    if request.user.is_authenticated:
        posts = posts.annotate(
            is_liked=Exists(Like.objects.filter(user=request.user, order=OuterRef('pk')))
        )
    else:
        posts = posts.annotate(is_liked=models.Value(False, output_field=models.BooleanField()))

    context = {
        'profile': profile,
        'promocodes': promocodes,
        'friends_count': friends_count,
        'friends_preview': friends_preview,
        'is_following': is_following,
        'is_friend': is_friend,
        'posts': posts,
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
