from django.conf import settings
from django.db import models
from django.db.models import Q


class TransactionKind(models.TextChoices):
    ACCRUAL = 'ACCRUAL', 'Начисление'
    ADJUST = 'ADJUST', 'Корректировка'
    SPEND = 'SPEND', 'Списание'


class PointsBalance(models.Model):
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
    def points(self) -> int:
        return (self.points10 or 0) // 10

    def __str__(self) -> str:
        return f'Balance(user={self.user_id}, points10={self.points10})'


class PointsTransaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_transactions',
    )
    order = models.ForeignKey(
        'add_order.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_transactions',
    )

    amount10 = models.IntegerField()
    kind = models.CharField(
        max_length=20,
        choices=TransactionKind.choices,
        default=TransactionKind.ACCRUAL,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def amount_points(self) -> int:
        a = self.amount10 or 0
        return a // 10 if a >= 0 else -((-a) // 10)

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
    class RewardType(models.TextChoices):
        COFFEE = 'COFFEE', 'Кофе'
        DESSERT = 'DESSERT', 'Десерт'
        DISCOUNT = 'DISCOUNT', 'Скидка'
        DRINK = 'DRINK', 'Напиток'
        MEAL = 'MEAL', 'Еда'
        COMBO = 'COMBO', 'Комбо'

    class Rarity(models.TextChoices):
        COMMON = 'COMMON', 'Обычный'
        RARE = 'RARE', 'Редкий'
        LEGENDARY = 'LEGENDARY', 'Легендарный'

    title = models.CharField('Название', max_length=120)
    description = models.TextField('Описание', blank=True)

    reward_type = models.CharField(
        'Тип награды',
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.DISCOUNT,
    )
    rarity = models.CharField(
        'Редкость',
        max_length=12,
        choices=Rarity.choices,
        default=Rarity.COMMON,
    )

    cafe = models.ForeignKey(
        'cafes.Cafe',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupon_offers',
        verbose_name='Кафе (если привязан)',
    )

    cost_points10 = models.PositiveIntegerField('Цена (баллы x10)', default=100)

    available_in_shop = models.BooleanField('Доступен в магазине', default=True)
    available_in_drop = models.BooleanField('Доступен в Drop', default=True)

    @property
    def rarity_code(self) -> str:
        return (self.rarity or self.Rarity.COMMON).lower()

    @property
    def reward_type_label(self) -> str:
        return self.get_reward_type_display()

    @property
    def rarity_display(self) -> str:
        return self.get_rarity_display()

    @property
    def display_title(self) -> str:
        return self.title or self.get_reward_type_display()

    @property
    def benefit_text(self) -> str:
        return self.description.strip() if self.description else self.display_title

    @property
    def cafe_name(self) -> str:
        return self.cafe.name if self.cafe else ''

    @property
    def expires_hint(self) -> str:
        if self.expires_in_days:
            return f'Срок: {self.expires_in_days} дн. после покупки'
        return 'Без срока'

    @property
    def cost_points(self) -> int:
        return (self.cost_points10 or 0) // 10

    @property
    def price_display(self) -> str:
        return f'{self.cost_points} баллов'

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
        indexes = [
            models.Index(fields=['is_active', 'available_in_shop', 'reward_type', 'rarity']),
            models.Index(fields=['is_active', 'available_in_drop', 'rarity']),
        ]

    def __str__(self) -> str:
        return self.title
