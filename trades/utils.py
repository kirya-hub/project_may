from __future__ import annotations

from django.db.models import Prefetch

from .models import TradeActivity, TradeItem


def trade_items_prefetch() -> Prefetch:
    return Prefetch(
        'trade__items',
        queryset=TradeItem.objects.select_related(
            'promocode',
            'promocode__source_offer',
            'promocode__source_offer__cafe',
        ).order_by('id'),
    )


def decorate_trade_activity(activity: TradeActivity) -> TradeActivity:
    items = list(activity.trade.items.all())
    offered = [item.promocode for item in items if item.side == TradeItem.Side.OFFERED]
    requested = [item.promocode for item in items if item.side == TradeItem.Side.REQUESTED]
    activity.offered_preview = offered[:1]
    activity.requested_preview = requested[:1]
    activity.extra_offered_count = max(0, len(offered) - 1)
    activity.extra_requested_count = max(0, len(requested) - 1)
    return activity
