from __future__ import annotations

from .models import TradeOffer


def inbox_badge(request):

    if not request.user.is_authenticated:
        return {'inbox_badge_count': 0}

    count = TradeOffer.objects.filter(
        to_user=request.user,
        status=TradeOffer.Status.PENDING,
    ).count()
    return {'inbox_badge_count': count}
