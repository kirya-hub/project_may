from django.contrib import admin
from django.contrib.admin import actions as admin_actions

from .models import FeedEvent, Like, Comment


@admin.register(FeedEvent)
class FeedEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'rarity', 'cafe', 'text', 'created_at')
    list_filter = ('kind', 'rarity', 'cafe', 'created_at')
    search_fields = ('user__username', 'text', 'cafe__name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    actions = ('delete_selected_feed_events',)

    def delete_selected_feed_events(self, request, queryset):
        return admin_actions.delete_selected(self, request, queryset)

    delete_selected_feed_events.short_description = 'Удалить выбранные события ленты'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order', 'created_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order', 'text', 'created_at')
