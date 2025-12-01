from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)

    check_image = models.ImageField(upload_to='orders/checks/')
    dish_photo = models.ImageField(upload_to='orders/photos/', blank=True, null=True)

    comment = models.TextField(blank=True, null=True)

    place_name = models.CharField(max_length=255, blank=True, null=True)
    total_sum = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    parsed_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Заказ #{self.id} от {self.user}"
