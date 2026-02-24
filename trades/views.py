from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from friends.services import friends_qs
from user_profile.models import Profile, PromoCode

from .forms import TradeOfferForm
from .models import TradeActivity, TradeItem, TradeOffer
from .services import (
    CouponNotAvailable,
    InvalidRatio,
    NotFriends,
    TradeError,
    accept_trade,
    cancel_trade,
    create_trade_offer,
    decline_trade,
)


@login_required
def trade_home(request):
    me = request.user

    incoming = (
        TradeOffer.objects.filter(to_user=me)
        .select_related('from_user')
        .prefetch_related('items', 'items__promocode')
        .order_by('-created_at')[:30]
    )
    outgoing = (
        TradeOffer.objects.filter(from_user=me)
        .select_related('to_user')
        .prefetch_related('items', 'items__promocode')
        .order_by('-created_at')[:30]
    )

    return render(request, 'trades/home.html', {'incoming': incoming, 'outgoing': outgoing})


@login_required
def trade_new(request, username: str):
    to_user = get_object_or_404(User, username=username)

    if to_user == request.user:
        messages.error(request, 'Нельзя обмениваться с самим собой')
        return redirect('trades:home')

    if not friends_qs(request.user).filter(id=to_user.id).exists():
        messages.error(request, 'Обмен доступен только между друзьями (взаимная подписка)')
        return redirect('trades:home')

    from_profile, _ = Profile.objects.get_or_create(user=request.user)
    to_profile, _ = Profile.objects.get_or_create(user=to_user)

    today = timezone.localdate()

    busy_ids = TradeItem.objects.filter(trade__status=TradeOffer.Status.PENDING).values_list(
        'promocode_id', flat=True
    )

    offered_qs = (
        PromoCode.objects.filter(
            profile=from_profile,
            status=PromoCode.Status.ACTIVE,
        )
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=today))
        .exclude(id__in=busy_ids)
        .order_by('-acquired_at')
    )

    requested_qs = (
        PromoCode.objects.filter(
            profile=to_profile,
            status=PromoCode.Status.ACTIVE,
        )
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=today))
        .exclude(id__in=busy_ids)
        .order_by('-acquired_at')
    )

    if request.method == 'POST':
        form = TradeOfferForm(request.POST, offered_qs=offered_qs, requested_qs=requested_qs)
        if form.is_valid():
            try:
                trade = create_trade_offer(
                    from_user=request.user,
                    to_user=to_user,
                    offered_ids=[c.id for c in form.cleaned_data['offered']],
                    requested_ids=[c.id for c in form.cleaned_data['requested']],
                    message=form.cleaned_data.get('message', ''),
                )
                messages.success(request, 'Предложение обмена отправлено ✅')
                return redirect('trades:detail', trade_id=trade.id)
            except (NotFriends, InvalidRatio, CouponNotAvailable, TradeError) as e:
                messages.error(request, str(e))
    else:
        form = TradeOfferForm(offered_qs=offered_qs, requested_qs=requested_qs)

    return render(request, 'trades/new.html', {'to_user': to_user, 'form': form})


@login_required
def trade_detail(request, trade_id: int):
    trade = get_object_or_404(
        TradeOffer.objects.select_related('from_user', 'to_user').prefetch_related(
            'items', 'items__promocode'
        ),
        id=trade_id,
    )

    if request.user.id not in (trade.from_user_id, trade.to_user_id):
        messages.error(request, 'Нет доступа к этому обмену')
        return redirect('trades:home')

    offered = [i.promocode for i in trade.items.all() if i.side == TradeItem.Side.OFFERED]
    requested = [i.promocode for i in trade.items.all() if i.side == TradeItem.Side.REQUESTED]

    next_url = request.GET.get('next') or reverse('trades:activity')

    return render(
        request,
        'trades/detail.html',
        {
            'trade': trade,
            'offered': offered,
            'requested': requested,
            'show_back': True,
            'header_back_url': next_url,
        },
    )


@login_required
def trade_accept(request, trade_id: int):
    if request.method != 'POST':
        return redirect('trades:detail', trade_id=trade_id)

    trade = get_object_or_404(TradeOffer, id=trade_id)
    try:
        accept_trade(request.user, trade)
        messages.success(request, 'Обмен принят ✅ Купоны обменяны')
    except (CouponNotAvailable, TradeError) as e:
        messages.error(request, str(e))
    return redirect('trades:detail', trade_id=trade_id)


@login_required
def trade_decline(request, trade_id: int):
    if request.method != 'POST':
        return redirect('trades:detail', trade_id=trade_id)

    trade = get_object_or_404(TradeOffer, id=trade_id)
    try:
        decline_trade(request.user, trade)
        messages.info(request, 'Обмен отклонён')
    except TradeError as e:
        messages.error(request, str(e))
    return redirect('trades:detail', trade_id=trade_id)


@login_required
def trade_cancel(request, trade_id: int):
    if request.method != 'POST':
        return redirect('trades:detail', trade_id=trade_id)

    trade = get_object_or_404(TradeOffer, id=trade_id)
    try:
        cancel_trade(request.user, trade)
        messages.info(request, 'Предложение отменено')
    except TradeError as e:
        messages.error(request, str(e))
    return redirect('trades:detail', trade_id=trade_id)


@login_required
def trade_activity(request):
    friend_ids = list(friends_qs(request.user).values_list('id', flat=True))

    events = (
        TradeActivity.objects.select_related('actor', 'trade', 'trade__from_user', 'trade__to_user')
        .filter(
            Q(trade__from_user_id__in=friend_ids)
            | Q(trade__to_user_id__in=friend_ids)
            | Q(trade__from_user=request.user)
            | Q(trade__to_user=request.user)
        )
        .order_by('-created_at')[:60]
    )

    next_url = request.GET.get('next') or reverse('home')

    return render(
        request,
        'trades/activity.html',
        {
            'events': events,
            'show_back': True,
            'header_back_url': next_url,
        },
    )
