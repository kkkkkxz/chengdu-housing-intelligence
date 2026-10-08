from django.contrib import admin
from .models import User, UserLoginLog

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'user_type', 'is_verified', 'created_at')
    list_filter = ('user_type', 'is_verified', 'gender', 'created_at')
    search_fields = ('username', 'email', 'phone', 'nike_name')
    ordering = ('-created_at',)

@admin.register(UserLoginLog)
class UserLoginLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_time', 'is_success')
    list_filter = ('is_success', 'login_time')
    search_fields = ('user__username', 'ip_address')
    ordering = ('-login_time',)
