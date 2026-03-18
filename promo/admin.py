from django.contrib import admin

from .models import CouponOffer, PointsTransaction


@admin.register(CouponOffer)
class CouponOfferAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'reward_type',
        'rarity',
        'cafe',
        'cost_points10',
        'available_in_shop',
        'available_in_drop',
        'expires_in_days',
        'is_active',
        'created_at',
    )
    list_filter = (
        'is_active',
        'reward_type',
        'rarity',
        'available_in_shop',
        'available_in_drop',
        'cafe',
    )
    search_fields = ('title', 'description', 'cafe__name')


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'amount10', 'order', 'created_at')
    list_filter = ('kind',)
    search_fields = ('user__username', 'user__email')
