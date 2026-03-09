from django.conf import settings
from django.db import models

from add_order.models import Order
from cafes.models import Cafe


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='order_likes',
    )
    order = models.ForeignKey(
        Order,
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
        Order,
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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feed_events',
    )

    kind = models.CharField(max_length=20, choices=Kind.choices)

    cafe = models.ForeignKey(
        Cafe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feed_events',
    )

    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'FeedEvent({self.kind}) {self.user_id}: {self.text}'
