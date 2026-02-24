from __future__ import annotations

from django.conf import settings
from django.db import models

from user_profile.models import PromoCode


class TradeOffer(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Ожидает ответа'
        ACCEPTED = 'ACCEPTED', 'Принят'
        DECLINED = 'DECLINED', 'Отклонён'
        CANCELLED = 'CANCELLED', 'Отменён'

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trade_offers_sent',
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trade_offers_received',
    )

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    message = models.CharField(max_length=240, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['to_user', 'status', '-created_at']),
            models.Index(fields=['from_user', 'status', '-created_at']),
        ]

    def __str__(self) -> str:
        return f'TradeOffer({self.pk}) {self.from_user_id}->{self.to_user_id} {self.status}'

    @property
    def is_pending(self) -> bool:
        return self.status == self.Status.PENDING


class TradeItem(models.Model):
    class Side(models.TextChoices):
        OFFERED = 'OFFERED', 'Отдаю'
        REQUESTED = 'REQUESTED', 'Хочу'

    trade = models.ForeignKey(TradeOffer, on_delete=models.CASCADE, related_name='items')

    promocode = models.ForeignKey(
        PromoCode,
        on_delete=models.PROTECT,
        related_name='trade_items',
    )

    side = models.CharField(max_length=10, choices=Side.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['trade', 'promocode'], name='uniq_trade_promocode'),
        ]

    def __str__(self) -> str:
        return f'TradeItem({self.trade_id}) {self.side} coupon={self.promocode_id}'


class TradeActivity(models.Model):
    class Kind(models.TextChoices):
        CREATED = 'CREATED', 'Создано предложение'
        ACCEPTED = 'ACCEPTED', 'Обмен принят'
        DECLINED = 'DECLINED', 'Обмен отклонён'
        CANCELLED = 'CANCELLED', 'Обмен отменён'

    kind = models.CharField(max_length=10, choices=Kind.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trade_activities',
    )
    trade = models.ForeignKey(TradeOffer, on_delete=models.CASCADE, related_name='activities')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['kind', '-created_at']),
        ]

    def __str__(self) -> str:
        return f'Activity({self.kind}) trade={self.trade_id} actor={self.actor_id}'
