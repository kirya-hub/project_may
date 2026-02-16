from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import DropWeek
from .services import choose_option, get_or_create_week


@login_required
def drops_page(request):
    drop_week = get_or_create_week(request.user)

    context = {
        'drop_week': drop_week,
        'options': drop_week.options.select_related('cafe', 'reward_offer'),
    }
    return render(request, 'drops/drops_page.html', context)


@login_required
def choose_drop(request, option_id: int):
    drop_week = get_or_create_week(request.user)

    if drop_week.status != DropWeek.Status.CHOOSING:
        return redirect('drops_page')

    choose_option(drop_week, option_id)
    return redirect('drops_page')
