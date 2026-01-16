from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

class Exam(models.Model):
    name = models.CharField(max_length=255)
    banner = models.ImageField(upload_to='exams/banners/')
    description = models.TextField()
    eligibility = models.TextField()
    exam_date = models.DateTimeField()
    location = models.CharField(max_length=255, default='Main Examination Center, Block A')
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_registration_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validation rule: Exam date can be modified only if the exam is more than 10 days away
        if self.pk:
            old_exam = Exam.objects.get(pk=self.pk)
            if old_exam.exam_date != self.exam_date:
                if (old_exam.exam_date - timezone.now()).days < 10:
                    raise ValidationError("Exam date can be modified only if the exam is more than 10 days away.")
        
        if self.exam_date < timezone.now():
            raise ValidationError("Exam date cannot be in the past.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
