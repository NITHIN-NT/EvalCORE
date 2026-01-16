from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Exam

@login_required
def exam_list(request):
    from registrations.models import Registration
    exams = Exam.objects.all().order_by('-exam_date')
    
    # Get all registrations for the current user
    user_registrations = {reg.exam_id: reg for reg in Registration.objects.filter(student=request.user)}
    
    from django.utils import timezone
    now = timezone.now()
    
    # Attach status and countdown to each exam
    for exam in exams:
        exam.user_registration = user_registrations.get(exam.id)
        delta = exam.exam_date - now
        exam.days_left = delta.days if delta.days >= 0 else 0
        
    return render(request, 'exams/exam_list.html', {'exams': exams})
