from django.conf import settings
from django.db import models

from add_order.models import Order


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
