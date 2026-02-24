from django.conf import settings
from django.db import models
from django.db.models import Q

from add_order.models import Order
from cafes.models import Cafe


class TransactionKind(models.TextChoices):
    ACCRUAL = 'ACCRUAL', 'Начисление'
    ADJUST = 'ADJUST', 'Корректировка'
    SPEND = 'SPEND', 'Списание'


class PointsBalance(models.Model):
    """Текущий баланс пользователя (в баллах x10, чтобы хранить без float)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_balance',
    )
    points10 = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Баланс'
        verbose_name_plural = 'Балансы'

    @property
    def points(self) -> float:
        return (self.points10 or 0) / 10

    def __str__(self) -> str:
        return f'Balance(user={self.user_id}, points10={self.points10})'


class PointsTransaction(models.Model):
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

    # положительное = начисление/корректировка, отрицательное = списание
    amount10 = models.IntegerField()
    kind = models.CharField(
        max_length=20,
        choices=TransactionKind.choices,
        default=TransactionKind.ACCRUAL,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def amount_points(self) -> float:
        return (self.amount10 or 0) / 10

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'kind', '-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['order'],
                condition=Q(kind=TransactionKind.ACCRUAL),
                name='uniq_points_accrual_per_order',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user_id}: {self.kind} {self.amount10}/10'


class CouponOffer(models.Model):
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

    cost_points10 = models.PositiveIntegerField('Цена (баллы x10)', default=100)

    @property
    def cost_points(self) -> float:
        return (self.cost_points10 or 0) / 10

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

    def __str__(self) -> str:
        return self.title
