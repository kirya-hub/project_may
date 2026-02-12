from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db import models


from .models import Follow
from .services import with_follow_flags, friends_qs

User = get_user_model()


@login_required
def friends_page(request):
    tab = request.GET.get("tab", "friends")
    q = (request.GET.get("q") or "").strip()

    base = User.objects.exclude(id=request.user.id).select_related("profile")

    base = with_follow_flags(base, request.user)

    if q:
        users = base.filter(
            models.Q(username__icontains=q) | models.Q(profile__name__icontains=q)
        ).order_by("username")

    else:
        if tab == "friends":
            users = friends_qs(request.user).exclude(id=request.user.id).select_related("profile")
            users = with_follow_flags(users, request.user)

        elif tab == "following":
            users = base.filter(is_following=True, is_follower=False).order_by("username")

        elif tab == "followers":
            users = base.filter(is_follower=True, is_following=False).order_by("username")

        else:
            return HttpResponseBadRequest("Unknown tab")

    popular = (
        User.objects.exclude(id=request.user.id)
        .select_related("profile")
        .annotate(followers_count=Count("follower_relations"))
        .order_by("-followers_count", "username")[:10]
    )
    popular = with_follow_flags(popular, request.user)

    friends_count = friends_qs(request.user).count()

    return render(
        request,
        "friends/friends_page.html",
        {
            "tab": tab,
            "q": q,
            "users": users,
            "popular": popular,
            "friends_count": friends_count,
        },
    )


@require_POST
@login_required
def follow_toggle(request, user_id: int):
    target = get_object_or_404(User, id=user_id)

    if target.id == request.user.id:
        return redirect(reverse("friends:friends_page"))

    rel = Follow.objects.filter(follower=request.user, following=target)
    if rel.exists():
        rel.delete()
    else:
        Follow.objects.create(follower=request.user, following=target)

    next_url = request.POST.get("next") or reverse("friends:friends_page")
    return redirect(next_url)
