from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import AvatarForm


@login_required
def my_profile(request):
    return redirect('profile_by_username', username=request.user.username)


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


def profile_home(request):
    if request.user.is_authenticated:
        return redirect('my_profile')
    return render(request, 'user_profile/profile_guest.html')
    

@login_required
def edit_avatar(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = AvatarForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('my_profile')
    else:
        form = AvatarForm(instance=profile)

    return render(request, 'user_profile/edit_avatar.html', {'form': form})
