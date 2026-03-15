from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'cafe',
        'rating',
        'total_sum',
        'is_duplicate',
        'duplicate_reason',
        'duplicate_source_order',
        'created_at',
    )
    list_filter = ('created_at', 'user', 'cafe', 'rating', 'is_duplicate', 'duplicate_reason')
    search_fields = (
        'comment',
        'place_name',
        'cafe__name',
        'check_sha256',
        'check_dhash',
        'receipt_number',
        'fiscal_number',
    )
