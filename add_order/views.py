from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from drops.services import try_complete_by_order
from promo.services import accrue_points_for_order

from .forms import OrderForm


@login_required
def add_order_page(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)

        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            # 1) начисляем баллы (ставит points_accrued=True если начисление прошло)
            accrue_points_for_order(order)

            # 2) пробуем закрыть Drop и выдать награду
            try_complete_by_order(order)

            messages.success(request, 'Заказ опубликован!')
            return redirect('add_order')
        else:
            messages.error(request, 'Проверь поля формы — есть ошибки.')
    else:
        form = OrderForm()

    return render(request, 'add_order/add_order.html', {'form': form})
