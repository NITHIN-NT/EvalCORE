from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from exams.models import Exam
from exams.forms import ExamForm
from registrations.models import Registration
from registrations.utils import send_status_email
from accounts.forms import LoginForm

def staff_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_panel:login')
        if not request.user.is_staff:
            messages.error(request, "Access denied. Admins only.")
            return redirect('admin_panel:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_panel:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user and user.is_staff:
                login(request, user)
                messages.success(request, f"Admin access granted. Welcome, {user.first_name}!")
                return redirect('admin_panel:dashboard')
            elif user:
                messages.error(request, "Access denied. This portal is for administrators only.")
            else:
                messages.error(request, "Invalid administrator credentials.")
    else:
        form = LoginForm()
    return render(request, 'admin_panel/login.html', {'form': form})

@login_required
@staff_required
def admin_dashboard(request):
    counts = {
        'total': Registration.objects.count(),
        'pending': Registration.objects.filter(status='Pending').count(),
        'approved': Registration.objects.filter(status='Approved').count(),
        'rejected': Registration.objects.filter(status='Rejected').count(),
        'hold': Registration.objects.filter(status='Hold').count(),
    }
    registrations = Registration.objects.all().select_related('student', 'exam').order_by('-registered_at')
    return render(request, 'admin_panel/dashboard.html', {
        'registrations': registrations,
        'counts': counts
    })

@login_required
@staff_required
def admin_profile(request):
    return render(request, 'admin_panel/profile.html', {
        'user': request.user
    })

@login_required
@staff_required
def update_registration_status(request, reg_id, status):
    registration = get_object_or_404(Registration, id=reg_id)
    reason = request.POST.get('rejection_reason', '')
    
    if status not in ['Approved', 'Rejected', 'Hold']:
        messages.error(request, "Invalid status.")
        return redirect('admin_panel:dashboard')
    
    registration.status = status
    if status == 'Rejected' and reason:
        registration.rejection_reason = reason
    elif status == 'Hold' and reason:
        registration.hold_reason = reason
    
    registration.save()
    
    # Trigger automated email notification
    try:
        send_status_email(registration, status, reason=reason)
        messages.success(request, f"Registration for {registration.student.email} has been {status} and notification sent.")
    except Exception as e:
        messages.warning(request, f"Status updated to {status}, but email failed: {e}")
    
    return redirect('admin_panel:dashboard')

@login_required
@staff_required
def delete_registration(request, reg_id):
    if request.method == 'POST':
        registration = get_object_or_404(Registration, id=reg_id)
        email = registration.student.email
        registration.delete()
        messages.success(request, f"Registration for {email} has been deleted.")
    return redirect('admin_panel:dashboard')

@login_required
@staff_required
def exam_create(request):
    if request.method == 'POST':
        form = ExamForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam created successfully!")
            return redirect('admin_panel:exam_list')
    else:
        form = ExamForm()
    return render(request, 'admin_panel/exam_form.html', {'form': form, 'title': 'Create Exam'})

@login_required
@staff_required
def exam_update(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == 'POST':
        form = ExamForm(request.POST, request.FILES, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam updated successfully!")
            return redirect('admin_panel:exam_list')
    else:
        form = ExamForm(instance=exam)
    return render(request, 'admin_panel/exam_form.html', {'form': form, 'title': 'Update Exam'})

@login_required
@staff_required
def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, "Exam deleted successfully!")
        return redirect('admin_panel:exam_list')
    return render(request, 'admin_panel/exam_confirm_delete.html', {'exam': exam})

@login_required
@staff_required
def admin_exam_list(request):
    exams = Exam.objects.all().order_by('-exam_date')
    return render(request, 'admin_panel/exam_list.html', {'exams': exams})

@login_required
@staff_required
def registration_detail(request, reg_id):
    registration = get_object_or_404(Registration, id=reg_id)
    import os
    filename = os.path.basename(registration.document.name) if registration.document else "No Document"
    return render(request, 'admin_panel/registration_detail.html', {
        'registration': registration,
        'filename': filename
    })

@login_required
@staff_required
def exam_registrations(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    registrations = Registration.objects.filter(exam=exam).select_related('student')
    return render(request, 'admin_panel/exam_registrations.html', {
        'exam': exam,
        'registrations': registrations
    })

@login_required
@staff_required
def bulk_update_registrations(request, exam_id, status):
    if request.method == 'POST':
        exam = get_object_or_404(Exam, id=exam_id)
        registrations = Registration.objects.filter(exam=exam)
        
        if status == 'Approved':
            registrations = registrations.filter(status='Pending')
        elif status == 'Rejected':
            registrations = registrations.filter(status='Pending')
        
        count = 0
        reason = request.POST.get('bulk_reason', 'Bulk update by administrator')
        
        for reg in registrations:
            reg.status = status
            if status == 'Rejected':
                reg.rejection_reason = reason
            reg.save()
            try:
                send_status_email(reg, status, reason=reason)
            except:
                pass
            count += 1
            
        messages.success(request, f"Successfully processed {count} registrations for {exam.name}.")
    
    return redirect('admin_panel:exam_registrations', exam_id=exam_id)
