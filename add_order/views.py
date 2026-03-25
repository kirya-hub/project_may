from __future__ import annotations

import logging
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from drops.services import try_complete_by_order
from promo.services import accrue_points_for_order

from .forms import OrderForm
from .models import Order
from .services.receipt_validator import process_order_receipt

logger = logging.getLogger(__name__)

def _delete_order_files(order: Order) -> None:
    """Удаляет медиафайлы заказа с диска перед удалением объекта.

    Django НЕ удаляет файлы автоматически при delete() — без этого
    каждый дубликат оставлял бы чек и фото блюда навсегда в media/.
    """
    paths: list[str] = []
    if order.check_image:
        try:
            paths.append(order.check_image.path)
        except ValueError:
            pass
    if order.dish_photo:
        try:
            paths.append(order.dish_photo.path)
        except ValueError:
            pass

    order.delete()

    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.debug("Удалён медиафайл: %s", path)
        except OSError as exc:

            logger.warning("Не удалось удалить файл %s: %s", path, exc)

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
            except Exception as exc:
                logger.error(
                    "Ошибка обработки чека для заказа #%s user=%s: %s",
                    order.pk,
                    request.user.pk,
                    exc,
                    exc_info=True,
                )
                _delete_order_files(order)
                messages.warning(request, f'Чек не обработался, пост не создан: {exc}')
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
                logger.info(
                    "Дубликат чека: заказ #%s reason=%s user=%s",
                    order.pk,
                    order.duplicate_reason,
                    request.user.pk,
                )

                _delete_order_files(order)
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
