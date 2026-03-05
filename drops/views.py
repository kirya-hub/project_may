from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from user_profile.models import Profile

from .models import DropOption, DropWeek
from .services import choose_option, ensure_week_options


@login_required
def drops_page(request):
    profile = get_object_or_404(Profile, user=request.user)
    week = ensure_week_options(profile)

    options = DropOption.objects.filter(week=week).select_related('cafe', 'offer').order_by('id')

    context = {
        'week': week,
        'options': options,
    }
    return render(request, 'drops/drops_page.html', context)


@login_required
def choose_drop(request, option_id: int):
    profile = get_object_or_404(Profile, user=request.user)
    week = ensure_week_options(profile)

    if week.status != DropWeek.Status.CHOOSING:
        return redirect('drops:drops_page')

    choose_option(profile, option_id)
    return redirect('drops:drops_page')
