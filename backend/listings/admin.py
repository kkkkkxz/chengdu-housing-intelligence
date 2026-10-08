from django.contrib import admin
from .models import House, Favorite

# Register your models here.

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'district', 'total_price', 'area', 'rooms', 'halls', 'created_at')
    list_filter = ('city', 'district', 'building_type', 'decorate', 'created_at')
    search_fields = ('title', 'community', 'address')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'house', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'house__title')
    ordering = ('-created_at',)
