from django.contrib import admin
from .models import Profile, PromoCode


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar_preview', 'friends_count')
    search_fields = ('user__username',)

    def avatar_preview(self, obj):
        if obj.avatar:
            return "Есть"
        return "Нет"
    avatar_preview.short_description = "Аватар"

    def friends_count(self, obj):
        return obj.friends.count()
    friends_count.short_description = "Друзей"


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'expires_at', 'is_active')
    list_filter = ('is_active', 'expires_at')
    search_fields = ('code', 'user__user__username')
