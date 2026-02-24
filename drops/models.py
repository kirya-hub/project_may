from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from cafes.models import Cafe
from promo.models import CouponOffer


def week_start_for(d: timezone.datetime | None = None):
    day = timezone.localdate() if d is None else d.date()
    return day - timezone.timedelta(days=day.weekday())


class DropWeek(models.Model):
    class Status(models.TextChoices):
        CHOOSING = 'CHOOSING', 'Выбор'
        ACTIVE = 'ACTIVE', 'Активен'
        COMPLETED = 'COMPLETED', 'Завершён'
        EXPIRED = 'EXPIRED', 'Истёк'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='drop_weeks'
    )
    week_start = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CHOOSING)

    chosen_option = models.OneToOneField(
        'DropOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chosen_in_week',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'week_start'], name='uniq_dropweek_user_week')
        ]

    @property
    def expires_at(self):
        return self.week_start + timezone.timedelta(days=7)

    @property
    def seconds_left(self) -> int:
        now = timezone.now()
        end = timezone.make_aware(
            timezone.datetime.combine(self.expires_at, timezone.datetime.min.time())
        )
        return max(0, int((end - now).total_seconds()))

    @property
    def time_left_display(self) -> str:
        """
        Красивый таймер: дни + часы/минуты.
        Примеры: "05:12", "2д 03:10", "00:00"
        """
        total = self.seconds_left
        if total <= 0:
            return '00:00'

        days, rem = divmod(total, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)

        if days > 0:
            return f'{days}д {hours:02d}:{minutes:02d}'
        return f'{hours:02d}:{minutes:02d}'

    def __str__(self):
        return f'DropWeek({self.user_id}, {self.week_start}, {self.status})'


class DropOption(models.Model):
    class Rarity(models.TextChoices):
        COMMON = 'COMMON', 'Обычный'
        RARE = 'RARE', 'Редкий'
        LEGENDARY = 'LEGENDARY', 'Легендарный'

    drop_week = models.ForeignKey(DropWeek, on_delete=models.CASCADE, related_name='options')
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='drop_options')

    rarity = models.CharField(max_length=10, choices=Rarity.choices, default=Rarity.COMMON)

    reward_offer = models.ForeignKey(
        CouponOffer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drop_rewards',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'DropOption({self.cafe_id}, {self.rarity})'
