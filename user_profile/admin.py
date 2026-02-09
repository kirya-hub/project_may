from django.contrib import admin
from django.db.models import Count, OuterRef, Exists
from .models import Profile, PromoCode
from friends.models import Follow


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'avatar_preview', 'friends_count')
    search_fields = ('user__username', 'name')

    def avatar_preview(self, obj):
        return "Есть" if obj.avatar else "Нет"
    avatar_preview.short_description = "Аватар"

    def friends_count(self, obj):
        """
        Друзья = взаимная подписка.
        Считаем так:
        друзья = сколько пользователей, на кого подписан obj.user,
        и которые подписаны на obj.user.
        """
        user = obj.user
        # мои подписки
        following_ids = Follow.objects.filter(follower=user).values_list("following_id", flat=True)
        # кто подписан на меня
        followers_ids = Follow.objects.filter(following=user).values_list("follower_id", flat=True)
        # взаимное пересечение
        return Follow.objects.filter(follower=user, following_id__in=followers_ids).count()

    friends_count.short_description = "Друзей"


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'expires_at', 'is_active')
    list_filter = ('is_active', 'expires_at')
    search_fields = ('code', 'user__user__username')
