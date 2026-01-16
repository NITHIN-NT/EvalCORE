from django.contrib import admin
from .models import Exam

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_date', 'location', 'fees', 'is_registration_open', 'created_at')
    search_fields = ('name', 'location')
    list_filter = ('is_registration_open', 'exam_date')
    ordering = ('-exam_date',)
