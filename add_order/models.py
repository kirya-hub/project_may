from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Order(models.Model):
    class DuplicateReason(models.TextChoices):
        NONE = '', 'Нет'
        EXACT_IMAGE = 'exact_image', 'Точный дубль изображения'
        IMAGE_SIMILAR = 'image_similar', 'Похожее изображение'
        CONTENT_MATCH = 'content_match', 'Совпадение по содержимому чека'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)

    check_image = models.ImageField(upload_to='orders/checks/')
    dish_photo = models.ImageField(upload_to='orders/photos/', blank=True, null=True)

    comment = models.TextField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка',
    )

    cafe = models.ForeignKey(
        'cafes.Cafe',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Кафе',
    )

    points_accrued = models.BooleanField(default=False)

    place_name = models.CharField(max_length=255, blank=True, null=True)
    total_sum = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    parsed_data = models.JSONField(blank=True, null=True)

    duplicate_signature = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_index=True,
        verbose_name='Сигнатура дубля',
    )
    check_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_index=True,
        verbose_name='SHA256 чека',
    )
    check_dhash = models.CharField(
        max_length=16,
        blank=True,
        default='',
        db_index=True,
        verbose_name='dHash чека',
    )
    content_signature = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_index=True,
        verbose_name='Сигнатура содержимого',
    )

    receipt_date = models.CharField(max_length=32, blank=True, default='', verbose_name='Дата чека')
    receipt_time = models.CharField(
        max_length=32, blank=True, default='', verbose_name='Время чека'
    )
    receipt_number = models.CharField(
        max_length=64, blank=True, default='', verbose_name='Номер чека'
    )
    fiscal_number = models.CharField(
        max_length=64, blank=True, default='', verbose_name='Фискальный номер'
    )

    is_duplicate = models.BooleanField(
        default=False,
        verbose_name='Дубликат чека',
    )
    duplicate_reason = models.CharField(
        max_length=32,
        blank=True,
        default='',
        choices=DuplicateReason.choices,
        verbose_name='Причина дубля',
    )
    duplicate_source_order = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duplicate_attempts',
        verbose_name='Исходный заказ-дубль',
    )

    def __str__(self):
        return f'Заказ #{self.id} от {self.user}'
