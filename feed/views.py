from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from add_order.models import Order

from .models import FeedEvent, Like


def feed_home(request):
    orders_qs = Order.objects.select_related('user', 'user__profile', 'cafe').order_by(
        '-created_at'
    )
    orders_qs = orders_qs.annotate(likes_count=Count('likes', distinct=True))

    if request.user.is_authenticated:
        orders_qs = orders_qs.annotate(
            is_liked=Exists(Like.objects.filter(user=request.user, order=OuterRef('pk')))
        )
    else:
        orders_qs = orders_qs.annotate(
            is_liked=models.Value(False, output_field=models.BooleanField())
        )

    events_qs = FeedEvent.objects.select_related('user', 'user__profile', 'cafe').order_by(
        '-created_at'
    )[:30]

    orders = list(orders_qs[:40])
    events = list(events_qs)

    items: list[dict] = []
    for o in orders:
        items.append({'type': 'order', 'obj': o, 'created_at': o.created_at})
    for e in events:
        items.append({'type': 'event', 'obj': e, 'created_at': e.created_at})

    items.sort(key=lambda x: x['created_at'], reverse=True)
    items = items[:50]

    return render(request, 'feed/feed_home.html', {'items': items})


@require_POST
@login_required
def toggle_like(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)

    like, created = Like.objects.get_or_create(user=request.user, order=order)
    if not created:
        like.delete()

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'home'
    return redirect(next_url)
