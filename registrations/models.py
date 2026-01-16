from django.db import models
from django.conf import settings
from exams.models import Exam

class Registration(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='registrations')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='registrations')
    document = models.FileField(upload_to='registrations/documents/')
    registered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending', choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Hold', 'Hold'),
    ])
    registration_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    hold_reason = models.TextField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, default='Pending', choices=[
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ])
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student.email} - {self.exam.name}"
