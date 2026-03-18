from django.contrib import admin

from friends.models import Follow

from .models import Profile, PromoCode


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'avatar_preview', 'friends_count')
    search_fields = ('user__username', 'name')

    def avatar_preview(self, obj):
        return 'Есть' if obj.avatar else 'Нет'

    avatar_preview.short_description = 'Аватар'

    def friends_count(self, obj):
        user = obj.user
        followers_ids = Follow.objects.filter(following=user).values_list('follower_id', flat=True)
        return Follow.objects.filter(follower=user, following_id__in=followers_ids).count()

    friends_count.short_description = 'Друзей'


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'profile', 'origin', 'status', 'expires_at', 'acquired_at', 'used_at')
    list_filter = ('origin', 'status', 'expires_at')
    search_fields = ('code', 'profile__user__username')
