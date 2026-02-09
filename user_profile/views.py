from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import models

from .models import Profile
from .forms import ProfileEditForm

from friends.models import Follow
from friends.services import friends_qs


@login_required
def my_profile(request):
    return redirect('profile_by_username', username=request.user.username)


def profile_detail(request, username=None, user_id=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = get_object_or_404(User, id=user_id)

    profile = get_object_or_404(Profile, user=user)

    today = timezone.now().date()
    promocodes = profile.promocodes.filter(is_active=True).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=today)
    )

    # друзья = взаимная подписка
    friends_count = friends_qs(user).count()

    # превью аватарок (ТОЛЬКО для своего профиля)
    friends_preview = []
    if request.user.is_authenticated and request.user == user:
        friends_preview = (
            friends_qs(request.user)
            .select_related("profile")[:3]
        )

    # статусы подписки
    is_following = False
    is_friend = False

    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()

        is_follower = Follow.objects.filter(
            follower=user,
            following=request.user
        ).exists()

        is_friend = is_following and is_follower

    context = {
        "profile": profile,
        "promocodes": promocodes,
        "friends_count": friends_count,
        "friends_preview": friends_preview,
        "is_following": is_following,
        "is_friend": is_friend,
    }

    return render(request, "user_profile/profile_detail.html", context)


def profile_home(request):
    if request.user.is_authenticated:
        return redirect("my_profile")
    return render(request, "user_profile/profile_guest.html")


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("my_profile")
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, "user_profile/edit_profile.html", {"form": form})
