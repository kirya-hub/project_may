from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import DropOption, DropWeek
from .services import choose_option, ensure_week_options


@login_required
def drops_page(request):
    if request.GET.get('refresh') == '1':
        ensure_week_options(request.user)
        return redirect('drops:drops_page')

    week = ensure_week_options(request.user)

    options = (
        DropOption.objects.filter(drop_week=week)
        .select_related('cafe', 'reward_offer')
        .order_by('id')
    )

    return render(
        request,
        'drops/drops_page.html',
        {
            'drop_week': week,
            'options': options,
            'show_back': True,
        },
    )


@login_required
def choose_drop(request, option_id: int):
    if request.method != 'GET':
        return redirect('drops:drops_page')

    week = ensure_week_options(request.user)

    if week.status != DropWeek.Status.CHOOSING:
        return redirect('drops:drops_page')

    choose_option(request.user, option_id)
    return redirect('drops:drops_page')
