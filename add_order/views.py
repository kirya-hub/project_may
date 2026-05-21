from __future__ import annotations

import logging
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from promo.services import accrue_points_for_order, get_weekly_accrual_status
from user_profile.levels import grant_post_xp_once_per_day

from .forms import OrderForm
from .models import Order
from .services.receipt_validator import process_order_receipt

logger = logging.getLogger(__name__)


def _delete_order_files(order: Order) -> None:
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
            p = Path(path)
            if p.exists():
                p.unlink()
                logger.debug('Удалён медиафайл: %s', path)
        except OSError as exc:
            logger.warning('Не удалось удалить файл %s: %s', path, exc)


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
                    'Ошибка обработки чека для заказа #%s user=%s: %s',
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
                    'Дубликат чека: заказ #%s reason=%s user=%s',
                    order.pk,
                    order.duplicate_reason,
                    request.user.pk,
                )

                _delete_order_files(order)
                messages.warning(request, f'{message} Пост в ленте не создан.')
                return redirect('add_order')

            if order.total_sum is None:
                _delete_order_files(order)
                messages.warning(request, 'Позиции чека не совпали с меню кафе. Пост не создан.')
                return redirect('add_order')

            points_earned = accrue_points_for_order(order)
            weekly_used, weekly_limit = get_weekly_accrual_status(request.user)

            try:
                grant_post_xp_once_per_day(request.user)
            except Exception as exc:
                logger.warning('grant_post_xp failed for user=%s: %s', request.user.pk, exc)

            if points_earned > 0:
                points_display = points_earned // 10
                messages.success(
                    request,
                    f'Заказ опубликован! +{points_display} баллов. Чеков с кэшбэком на этой неделе: {weekly_used}/{weekly_limit}.'
                )
            elif weekly_used >= weekly_limit:
                messages.success(
                    request,
                    f'Заказ опубликован! Лимит кэшбэка на этой неделе исчерпан ({weekly_limit}/{weekly_limit}).'
                )
            else:
                messages.success(request, 'Заказ опубликован!')
            return redirect('add_order')
        else:
            messages.error(request, 'Проверь поля формы — есть ошибки.')
    else:
        form = OrderForm()

    return render(request, 'add_order/add_order.html', {'form': form})
