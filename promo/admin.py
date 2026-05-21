from django.contrib import admin
from django.utils.html import format_html

from .models import CouponOffer, PointsTransaction


class CouponOfferAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'description',
        'cafe',
        'reward_type',
        'rarity',
        'cost_points10',
        'is_active',
        'available_in_shop',
        'available_in_drop',
    )
    list_filter = (
        'is_active',
        'rarity',
        'reward_type',
        'available_in_shop',
        'available_in_drop',
        'cafe',
    )
    search_fields = ('description', 'cafe__name')
    list_editable = ('is_active', 'available_in_shop', 'available_in_drop')
    autocomplete_fields = ['cafe']

    readonly_fields = ('points_display',)

    fieldsets = (
        ('Основное', {'fields': ('cafe', 'image', 'description', 'reward_type', 'menu_item')}),
        (
            'Редкость и цена',
            {'fields': ('rarity', 'cost_points10', 'points_display', 'expires_in_days')},
        ),
        ('Доступность', {'fields': ('is_active', 'available_in_shop', 'available_in_drop')}),
    )

    def points_display(self, obj):
        if obj.cost_points10:
            return format_html('<b>{} баллов</b>', obj.cost_points10 // 10)
        return '—'

    points_display.short_description = 'Цена (баллы)'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'menu_item' in form.base_fields and obj and obj.cafe_id:
            form.base_fields['menu_item'].queryset = form.base_fields['menu_item'].queryset.filter(
                category__cafe=obj.cafe
            )
        return form

    class Media:
        js = ('admin/js/coupon_admin.js',)


admin.site.register(CouponOffer, CouponOfferAdmin)


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'amount10', 'order', 'created_at')
    list_filter = ('kind',)
    search_fields = ('user__username', 'user__email')
