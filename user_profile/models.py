from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


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

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self) -> str:
        return self.user.username

    @property
    def points(self) -> float:
        return (self.points10 or 0) / 10


class PromoCode(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Активен'
        USED = 'USED', 'Использован'
        EXPIRED = 'EXPIRED', 'Истёк'

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
        verbose_name='Купон из магазина',
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

    used_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Использован',
    )

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-acquired_at']

    def __str__(self) -> str:
        return f'{self.code} ({self.profile.user.username})'

    @property
    def is_expired(self) -> bool:

        if not self.expires_at:
            return False
        return self.expires_at < timezone.localdate()

    @property
    def expires_at_display(self) -> str:

        if not self.expires_at:
            return 'Без срока'

        today = timezone.localdate()

        if self.expires_at < today:
            return f'Истёк {self.expires_at.strftime("%d.%m.%Y")}'

        return f'До {self.expires_at.strftime("%d.%m.%Y")}'
