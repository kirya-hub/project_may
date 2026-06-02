#!/usr/bin/env python
"""
Запуск dev-сервера со сдвигом времени вперёд.

Использование:
    python run_faketime.py          # +7 дней (по умолчанию)
    python run_faketime.py 14       # +14 дней
    TIME_TRAVEL_DAYS=3 python run_faketime.py

Внимание: запускается с --noreload, поэтому автоперезагрузка не работает.
"""
import os
import sys
from datetime import date, timedelta

days = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('TIME_TRAVEL_DAYS', 7))
future = date.today() + timedelta(days=days)
target = future.isoformat()

print(f"[faketime] Сегодня:  {date.today()}")
print(f"[faketime] Симуляция: {future}  (+{days} дней)")
print(f"[faketime] --noreload активен, авто-рестарт отключён\n")

from freezegun import freeze_time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

with freeze_time(target, tick=True):
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'runserver', '--noreload'])
