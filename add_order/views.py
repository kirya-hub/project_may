from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from drops.services import try_complete_by_order
from promo.services import accrue_points_for_order

from .forms import OrderForm
from .services.receipt_validator import process_order_receipt


@login_required
def add_order_page(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)

        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            try:
                process_order_receipt(order)
            except Exception as e:
                messages.warning(request, f'Заказ сохранён, но чек не обработался: {e}')

            accrue_points_for_order(order)

            try_complete_by_order(order)

            messages.success(request, 'Заказ опубликован!')
            return redirect('add_order')
        else:
            messages.error(request, 'Проверь поля формы — есть ошибки.')
    else:
        form = OrderForm()

    return render(request, 'add_order/add_order.html', {'form': form})
