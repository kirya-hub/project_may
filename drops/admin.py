from django.contrib import admin

from .models import DropOption, DropWeek


class DropOptionInline(admin.TabularInline):
    model = DropOption
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(DropWeek)
class DropWeekAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'week_start',
        'status',
        'chosen_option',
        'options_count',
        'created_at',
    )
    list_filter = ('status', 'week_start', 'created_at')
    search_fields = ('user__username', 'options__cafe__name')
    ordering = ('-week_start', '-created_at')
    date_hierarchy = 'week_start'
    readonly_fields = ('created_at',)
    inlines = (DropOptionInline,)
    actions = ('delete_selected_drop_weeks',)

    def options_count(self, obj):
        return obj.options.count()

    options_count.short_description = 'Количество вариантов'

    def delete_selected_drop_weeks(self, request, queryset):
        deleted_count = queryset.count()
        queryset.delete()
        self.message_user(request, f'Удалено DropWeek: {deleted_count}.')

    delete_selected_drop_weeks.short_description = 'Удалить выбранные DropWeek'


@admin.register(DropOption)
class DropOptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'drop_week',
        'cafe',
        'rarity',
        'reward_offer',
        'created_at',
    )
    list_filter = ('rarity', 'cafe', 'created_at')
    search_fields = ('cafe__name', 'drop_week__user__username', 'reward_offer__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
