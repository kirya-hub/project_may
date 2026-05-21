from django.contrib import admin

from .models import FeedEvent, Like, Comment


@admin.register(FeedEvent)
class FeedEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'rarity', 'cafe', 'text', 'created_at')
    list_filter = ('kind', 'rarity', 'cafe')
    search_fields = ('user__username', 'text')
    ordering = ('-created_at',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order', 'created_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order', 'text', 'created_at')
