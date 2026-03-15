from django.contrib import admin

from .models import Cafe, CafeStaff, MenuCategory, MenuItem


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


class CafeStaffInline(admin.TabularInline):
    model = CafeStaff
    extra = 1
    autocomplete_fields = ('user',)


@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'working_hours')
    search_fields = ('name', 'address')
    inlines = [MenuCategoryInline, CafeStaffInline]


@admin.register(CafeStaff)
class CafeStaffAdmin(admin.ModelAdmin):
    list_display = ('cafe', 'user', 'created_at')
    search_fields = ('cafe__name', 'user__username', 'user__email')
    autocomplete_fields = ('cafe', 'user')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
