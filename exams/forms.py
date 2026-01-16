from django import forms
from .models import Exam

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'banner', 'description', 'eligibility', 'exam_date', 'location', 'fees', 'is_registration_open']
        widgets = {
            'exam_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
