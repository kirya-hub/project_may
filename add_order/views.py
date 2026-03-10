from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from drops.services import try_complete_by_order
from promo.services import accrue_points_for_order

from .forms import OrderForm
from .models import Order
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
                order.delete()
                messages.warning(request, f'Чек не обработался, пост не создан: {e}')
                return redirect('add_order')

            order = Order.objects.get(pk=order.pk)

            if order.is_duplicate:
                duplicate_reason_map = {
                    Order.DuplicateReason.EXACT_IMAGE: 'Этот чек уже был загружен раньше.',
                    Order.DuplicateReason.IMAGE_SIMILAR: 'Этот чек слишком похож на уже загруженный.',
                    Order.DuplicateReason.CONTENT_MATCH: 'Чек с такими данными уже был загружен раньше.',
                }
                message = duplicate_reason_map.get(
                    order.duplicate_reason,
                    'Этот чек уже был загружен раньше.',
                )
                order.delete()
                messages.warning(request, f'{message} Пост в ленте не создан.')
                return redirect('add_order')

            accrue_points_for_order(order)
            try_complete_by_order(order)

            messages.success(request, 'Заказ опубликован!')
            return redirect('add_order')
        else:
            messages.error(request, 'Проверь поля формы — есть ошибки.')
    else:
        form = OrderForm()

    return render(request, 'add_order/add_order.html', {'form': form})
