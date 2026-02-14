from django.contrib import admin
from .models import Cafe, MenuCategory, MenuItem


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'cafe')
    inlines = [MenuItemInline]


class MenuCategoryInline(admin.TabularInline):
    model = MenuCategory
    extra = 1


@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    inlines = [MenuCategoryInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
