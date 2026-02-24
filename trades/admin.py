from django.contrib import admin

from .models import TradeActivity, TradeItem, TradeOffer


class TradeItemInline(admin.TabularInline):
    model = TradeItem
    extra = 0


@admin.register(TradeOffer)
class TradeOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_user', 'to_user', 'status', 'created_at', 'responded_at')
    list_filter = ('status',)
    search_fields = ('from_user__username', 'to_user__username')
    inlines = [TradeItemInline]


@admin.register(TradeActivity)
class TradeActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'kind', 'actor', 'trade', 'created_at')
    list_filter = ('kind',)
    search_fields = ('actor__username',)
