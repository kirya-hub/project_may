from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from add_order.models import Order

from .models import Comment, FeedEvent, Like


def _comments_prefetch():
    return Prefetch(
        'comments',
        queryset=Comment.objects.select_related('user', 'user__profile').order_by('created_at'),
    )


def feed_home(request):
    orders_qs = (
        Order.objects.select_related('user', 'user__profile', 'cafe')
        .prefetch_related(_comments_prefetch())
        .order_by('-created_at')
        .annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
        )
    )

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
    liked = created
    if not created:
        like.delete()
        liked = False

    likes_count = Like.objects.filter(order=order).count()

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse(
            {
                'ok': True,
                'liked': liked,
                'likes_count': likes_count,
                'order_id': order.id,
            }
        )

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'home'
    return redirect(next_url)


@require_POST
@login_required
def add_comment(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)

    text = (request.POST.get('text') or '').strip()
    if not text:
        return JsonResponse({'ok': False, 'error': 'empty'}, status=400)

    if len(text) > 300:
        return JsonResponse({'ok': False, 'error': 'too_long'}, status=400)

    comment = Comment.objects.create(
        user=request.user,
        order=order,
        text=text,
    )

    comments_count = Comment.objects.filter(order=order).count()
    comment_html = render_to_string(
        'feed/_comment_item.html',
        {'comment': comment},
        request=request,
    )

    return JsonResponse(
        {
            'ok': True,
            'order_id': order.id,
            'comments_count': comments_count,
            'comment_html': comment_html,
        }
    )


@require_POST
@login_required
def delete_comment(request, comment_id: int):
    comment = get_object_or_404(Comment.objects.select_related('order'), pk=comment_id)

    if comment.user_id != request.user.id:
        return HttpResponseForbidden('forbidden')

    order_id = comment.order_id
    comment.delete()

    comments_count = Comment.objects.filter(order_id=order_id).count()

    return JsonResponse(
        {
            'ok': True,
            'order_id': order_id,
            'comment_id': comment_id,
            'comments_count': comments_count,
        }
    )
