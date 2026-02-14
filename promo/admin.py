from django.contrib import admin
from .models import PointsTransaction, CouponOffer


@admin.register(CouponOffer)
class CouponOfferAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'cafe',
        'cost_points10',
        'expires_in_days',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active', 'cafe')
    search_fields = ('title', 'description', 'cafe__name')


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'amount10', 'order', 'created_at')
    list_filter = ('kind',)
    search_fields = ('user__username',)
