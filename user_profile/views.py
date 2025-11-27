from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Profile


def profile_detail(request, username=None, user_id=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = get_object_or_404(User, id=user_id)

    profile = get_object_or_404(Profile, user=user)

    promocodes = profile.promocodes.all()

    context = {
        'profile': profile,
        'promocodes': promocodes
    }

    return render(request, 'user_profile/profile_detail.html', context)
