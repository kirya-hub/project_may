from django.db import models
from django.utils.text import slugify


class Cafe(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    avatar = models.ImageField(upload_to='cafes/avatars/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MenuCategory(models.Model):
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='categories')
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.ImageField(upload_to='cafes/menu_icons/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    image = models.ImageField(upload_to='cafes/menu_items/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.price}₽)"
