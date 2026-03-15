from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify

User = get_user_model()


class Cafe(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    avatar = models.ImageField(upload_to='cafes/avatars/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    working_hours = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    class Meta:
        verbose_name = 'Кафе'
        verbose_name_plural = 'Кафе'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or 'cafe'
            slug = base_slug
            index = 2
            while Cafe.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{index}'
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None

    def can_be_edited_by(self, user):
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return self.staff_members.filter(user=user).exists()


class MenuCategory(models.Model):
    cafe = models.ForeignKey(
        Cafe,
        on_delete=models.CASCADE,
        related_name='categories',
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.ImageField(upload_to='cafes/menu_icons/', blank=True, null=True)

    class Meta:
        verbose_name = 'Категория меню'
        verbose_name_plural = 'Категории меню'
        ordering = ['id']

    def __str__(self):
        return f'{self.cafe.name} — {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'category'
            slug = base_slug
            index = 2
            while MenuCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{index}'
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.CASCADE,
        related_name='items',
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    image = models.ImageField(upload_to='cafes/menu_items/', blank=True, null=True)

    class Meta:
        verbose_name = 'Позиция меню'
        verbose_name_plural = 'Позиции меню'
        ordering = ['id']

    def __str__(self):
        return self.name


class CafeStaff(models.Model):
    cafe = models.ForeignKey(
        Cafe,
        on_delete=models.CASCADE,
        related_name='staff_members',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cafe_staff_links',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Сотрудник кафе'
        verbose_name_plural = 'Сотрудники кафе'
        unique_together = ('cafe', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.cafe.name} — {self.user}'
