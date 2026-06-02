from django.contrib import admin
from django.db.models import Q

from .models import Order


class DishPhotoStateFilter(admin.SimpleListFilter):
    title = 'Фото блюда'
    parameter_name = 'dish_photo_state'

    def lookups(self, request, model_admin):
        return (
            ('with_photo', 'С фото'),
            ('without_photo', 'Без фото'),
        )

    def queryset(self, request, queryset):
        without_photo_query = Q(dish_photo='') | Q(dish_photo__isnull=True)

        if self.value() == 'with_photo':
            return queryset.exclude(without_photo_query)
        if self.value() == 'without_photo':
            return queryset.filter(without_photo_query)
        return queryset


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'cafe',
        'has_dish_photo',
        'has_comment',
        'rating',
        'total_sum',
        'is_duplicate',
        'points_accrued',
        'created_at',
    )
    list_filter = (
        DishPhotoStateFilter,
        'created_at',
        'user',
        'cafe',
        'rating',
        'is_duplicate',
        'duplicate_reason',
        'points_accrued',
    )
    search_fields = (
        'user__username',
        'comment',
        'place_name',
        'cafe__name',
        'receipt_number',
        'fiscal_number',
        'check_sha256',
        'check_dhash',
    )
    readonly_fields = (
        'created_at',
        'points_accrued',
        'parsed_data',
        'duplicate_signature',
        'check_sha256',
        'check_dhash',
        'content_signature',
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    actions = ('delete_orders_without_dish_photo',)

    def has_dish_photo(self, obj):
        return bool(obj.dish_photo)

    has_dish_photo.boolean = True
    has_dish_photo.short_description = 'Фото блюда'

    def has_comment(self, obj):
        return bool(obj.comment)

    has_comment.boolean = True
    has_comment.short_description = 'Комментарий'

    def delete_orders_without_dish_photo(self, request, queryset):
        without_photo_query = Q(dish_photo='') | Q(dish_photo__isnull=True)
        orders_without_photo = queryset.filter(without_photo_query)
        deleted_count = orders_without_photo.count()
        skipped_count = queryset.exclude(without_photo_query).count()

        orders_without_photo.delete()

        self.message_user(
            request,
            f'Удалено публикаций без фото: {deleted_count}. '
            f'Пропущено публикаций с фото: {skipped_count}.',
        )

    delete_orders_without_dish_photo.short_description = 'Удалить выбранные публикации без фото'
