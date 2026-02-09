from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )
    name = models.CharField(
        "Имя", 
        max_length=50, 
        blank=True, 
        default=""
    )


    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return self.user.username


class PromoCode(models.Model):
    user = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="promocodes",
        verbose_name="Профиль"
    )
    code = models.CharField(
        max_length=100,
        verbose_name="Промокод"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    expires_at = models.DateField(
        blank=True,
        null=True,
        verbose_name="Срок действия"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"

    def __str__(self):
        return f"{self.code} ({self.user.user.username})"
