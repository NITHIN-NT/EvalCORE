from django.contrib import admin
from .models import CustomUser, OTP

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_verified', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email',)
    list_filter = ('is_verified', 'is_staff', 'is_active')
    ordering = ('-date_joined',)

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'is_used')
    search_fields = ('user__email', 'code')
    list_filter = ('is_used', 'created_at')
