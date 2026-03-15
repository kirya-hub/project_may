from django.conf import settings
from django.db import models


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='order_likes',
    )
    order = models.ForeignKey(
        'add_order.Order',
        on_delete=models.CASCADE,
        related_name='likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'order'],
                name='unique_like_per_user',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user.pk} -> {self.order.pk}'


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feed_comments',
    )
    order = models.ForeignKey(
        'add_order.Order',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'Comment({self.user_id} -> {self.order_id})'


class FeedEvent(models.Model):
    class Kind(models.TextChoices):
        DROP_CHOSEN = 'DROP_CHOSEN', 'Выбор Drop'

    class Rarity(models.TextChoices):
        COMMON = 'COMMON', 'Обычный'
        RARE = 'RARE', 'Редкий'
        LEGENDARY = 'LEGENDARY', 'Легендарный'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feed_events',
    )

    kind = models.CharField(max_length=20, choices=Kind.choices)

    cafe = models.ForeignKey(
        'cafes.Cafe',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feed_events',
    )

    rarity = models.CharField(
        max_length=10,
        choices=Rarity.choices,
        default=Rarity.COMMON,
    )

    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'FeedEvent({self.kind}) {self.user_id}: {self.text}'
