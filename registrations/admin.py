from django.contrib import admin
from .models import Registration

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'student', 'exam', 'status', 'payment_status', 'registered_at')
    search_fields = ('registration_number', 'student__email', 'exam__name', 'razorpay_order_id')
    list_filter = ('status', 'payment_status', 'exam', 'registered_at')
    ordering = ('-registered_at',)
    readonly_fields = ('registration_number', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
