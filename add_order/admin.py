from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "cafe", "place_name", "comment", "created_at")
    list_filter = ("created_at", "user")
    search_fields = ("comment", "place_name", "cafe__name")
