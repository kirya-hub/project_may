from django.conf import settings
from django.db import models

from add_order.models import Order
from cafes.models import Cafe


class PointsTransaction(models.Model):
    class Kind(models.TextChoices):
        ACCRUAL = 'ACCRUAL', 'Начисление'
        ADJUST = 'ADJUST', 'Корректировка'
        SPEND = 'SPEND', 'Списание'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_transactions',
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_transactions',
    )

    amount10 = models.IntegerField()
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.ACCRUAL)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def amount_points(self):
        return (self.amount10 or 0) / 10

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'kind', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user_id}: {self.kind} {self.amount10}/10'


class CouponOffer(models.Model):
    """
    Купон в магазине (то, что можно купить за баллы).
    После покупки превращается в user_profile.PromoCode.
    """

    title = models.CharField('Название', max_length=120)
    description = models.TextField('Описание', blank=True)

    cafe = models.ForeignKey(
        Cafe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupon_offers',
        verbose_name='Кафе (если привязан)',
    )

    @property
    def cost_points(self):
        return (self.cost_points10 or 0) / 10

    cost_points10 = models.PositiveIntegerField('Цена (баллы x10)', default=100)

    expires_in_days = models.PositiveIntegerField(
        'Срок после покупки (дни)',
        null=True,
        blank=True,
        help_text='Если пусто — купон будет без срока',
    )

    is_active = models.BooleanField('В продаже', default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Купон (магазин)'
        verbose_name_plural = 'Купоны (магазин)'

    def __str__(self):
        return self.title
