from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from add_order.models import Order
from friends.services import friends_qs
from trades.models import TradeActivity, TradeItem

from .models import Comment, FeedEvent, Like


def _comments_prefetch():
    return Prefetch(
        'comments',
        queryset=Comment.objects.select_related('user', 'user__profile').order_by('created_at'),
    )


def _trade_items_prefetch():
    return Prefetch(
        'trade__items',
        queryset=TradeItem.objects.select_related(
            'promocode',
            'promocode__source_offer',
            'promocode__source_offer__cafe',
        ).order_by('id'),
    )


def _prepare_trade_activity(activity: TradeActivity) -> TradeActivity:
    trade_items = list(activity.trade.items.all())
    offered = [item.promocode for item in trade_items if item.side == TradeItem.Side.OFFERED]
    requested = [item.promocode for item in trade_items if item.side == TradeItem.Side.REQUESTED]
    activity.offered_preview = offered[:1]
    activity.requested_preview = requested[:1]
    activity.extra_offered_count = max(0, len(offered) - 1)
    activity.extra_requested_count = max(0, len(requested) - 1)
    return activity


def _item_key(item: dict) -> tuple[str, int]:
    return (item['type'], item['obj'].id)


def _is_friend_item(item: dict, friend_ids: set[int]) -> bool:
    obj = item['obj']
    if item['type'] in {'order', 'event'}:
        return obj.user_id in friend_ids
    if item['type'] == 'trade':
        return obj.trade.from_user_id in friend_ids or obj.trade.to_user_id in friend_ids
    return False


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

    trade_events_qs = (
        TradeActivity.objects.filter(kind=TradeActivity.Kind.ACCEPTED)
        .select_related(
            'actor',
            'actor__profile',
            'trade',
            'trade__from_user',
            'trade__from_user__profile',
            'trade__to_user',
            'trade__to_user__profile',
        )
        .prefetch_related(_trade_items_prefetch())
        .order_by('-created_at')[:30]
    )

    orders = list(orders_qs[:40])
    events = list(events_qs)
    trade_events = [_prepare_trade_activity(event) for event in trade_events_qs]

    items: list[dict] = []
    for o in orders:
        items.append({'type': 'order', 'obj': o, 'created_at': o.created_at})
    for e in events:
        items.append({'type': 'event', 'obj': e, 'created_at': e.created_at})
    for t in trade_events:
        items.append({'type': 'trade', 'obj': t, 'created_at': t.created_at})

    items.sort(key=lambda x: x['created_at'], reverse=True)
    items = items[:60]

    friend_items: list[dict] = []
    main_items = items

    if request.user.is_authenticated:
        friend_ids = set(friends_qs(request.user).values_list('id', flat=True))
        if friend_ids:
            friend_items = [item for item in items if _is_friend_item(item, friend_ids)][:8]
            pinned_keys = {_item_key(item) for item in friend_items}
            main_items = [item for item in items if _item_key(item) not in pinned_keys]

    return render(
        request,
        'feed/feed_home.html',
        {
            'items': main_items[:50],
            'friend_items': friend_items,
            'total_items_count': len(friend_items) + len(main_items[:50]),
        },
    )


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
        {'comment': comment, 'order_id': order.id},
        request=request,
    )

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if not is_ajax:
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'home'
        return redirect(next_url)

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
