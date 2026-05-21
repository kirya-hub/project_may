from __future__ import annotations

import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

_ACTIVATION_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    name = models.CharField(
        'Имя',
        max_length=50,
        blank=True,
        default='',
    )

    points10 = models.PositiveIntegerField(
        default=0,
        verbose_name='Баланс (x10)',
    )

    level = models.PositiveIntegerField(
        default=1,
        verbose_name='Уровень',
    )

    xp = models.PositiveIntegerField(
        default=0,
        verbose_name='Опыт',
    )

    last_trade_xp_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Дата последнего XP за обмен',
    )

    last_order_xp_date = models.DateField(null=True, blank=True)
    last_post_xp_date = models.DateField(null=True, blank=True)

    city = models.ForeignKey(
        'cafes.City',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='profiles',
        verbose_name='Город',
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self) -> str:
        return self.user.username

    @property
    def points(self) -> int:
        return (self.points10 or 0) // 10


class PromoCode(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Активен'
        USED = 'USED', 'Использован'
        EXPIRED = 'EXPIRED', 'Истёк'

    class Origin(models.TextChoices):
        SHOP = 'SHOP', 'Магазин'
        DROP = 'DROP', 'Drop'

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='promocodes',
        verbose_name='Профиль',
    )

    code = models.CharField(
        max_length=100,
        verbose_name='Промокод',
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )

    source_offer = models.ForeignKey(
        'promo.CouponOffer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_promocodes',
        verbose_name='Шаблон награды',
    )

    origin = models.CharField(
        max_length=10,
        choices=Origin.choices,
        default=Origin.SHOP,
        verbose_name='Источник',
    )

    acquired_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Получен',
    )

    expires_at = models.DateField(
        blank=True,
        null=True,
        verbose_name='Срок действия',
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус',
    )

    activation_code = models.CharField(
        max_length=4,
        blank=True,
        db_index=True,
        verbose_name='Код активации (4 символа)',
    )

    used_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Использован',
    )

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-acquired_at']

    def _generate_activation_code(self) -> str:
        for _ in range(20):
            code = ''.join(random.choices(_ACTIVATION_ALPHABET, k=4))
            if not PromoCode.objects.filter(
                activation_code=code,
                status=PromoCode.Status.ACTIVE,
            ).exclude(pk=self.pk).exists():
                return code
        return ''.join(random.choices(_ACTIVATION_ALPHABET, k=4))

    def save(self, *args, **kwargs):
        if not self.activation_code:
            self.activation_code = self._generate_activation_code()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.code} ({self.profile.user.username})'

    @property
    def rarity_code(self) -> str:
        if self.source_offer and self.source_offer.rarity:
            return self.source_offer.rarity.lower()
        return 'common'

    @property
    def reward_type_label(self) -> str:
        if self.source_offer:
            return self.source_offer.get_reward_type_display()
        return 'Купон'

    @property
    def rarity_display(self) -> str:
        if self.source_offer:
            return self.source_offer.get_rarity_display()
        return 'Обычный'

    @property
    def display_title(self) -> str:
        if self.source_offer and self.source_offer.title:
            return self.source_offer.title
        return self.code

    @property
    def benefit_text(self) -> str:
        if self.description:
            return self.description.strip()
        if self.source_offer and self.source_offer.description:
            return self.source_offer.description.strip()
        return self.display_title

    @property
    def cafe_name(self) -> str:
        if self.source_offer and self.source_offer.cafe:
            return self.source_offer.cafe.name
        return ''

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return self.expires_at < timezone.localdate()

    @property
    def is_shop_coupon(self) -> bool:
        return self.origin == self.Origin.SHOP

    @property
    def is_drop_coupon(self) -> bool:
        return self.origin == self.Origin.DROP

    @property
    def expires_at_display(self) -> str:
        if not self.expires_at:
            return 'Без срока'

        today = timezone.localdate()

        if self.expires_at < today:
            return f'Истёк {self.expires_at.strftime("%d.%m.%Y")}'

        return f'До {self.expires_at.strftime("%d.%m.%Y")}'

    @property
    def background_image(self):
        if not self.source_offer:
            return None
        offer = self.source_offer
        if offer.image:
            return offer.image
        if offer.menu_item_id and offer.menu_item.image:
            return offer.menu_item.image
        if offer.cafe_id and offer.cafe.coupon_bg:
            return offer.cafe.coupon_bg
        return None

    @property
    def background_focus(self):
        if not self.source_offer:
            return 'center'
        offer = self.source_offer
        if not offer.image and offer.menu_item_id and offer.menu_item.image:
            return offer.menu_item.image_focus or 'center'
        return 'center'
