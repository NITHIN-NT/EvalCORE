from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, LoginForm, OTPForm
from .models import CustomUser, OTP, Notification
from .utils import create_and_send_otp
from registrations.models import Registration

@login_required
def profile_view(request):
    registrations = Registration.objects.filter(student=request.user).select_related('exam')
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'registrations': registrations
    })

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = True  # We'll allow login but check is_verified
            user.save()
            if create_and_send_otp(user):
                request.session['otp_user_id'] = user.id
                messages.success(request, "Registration successful! Please verify your email with the OTP sent.")
                return redirect('verify_otp')
            else:
                messages.error(request, "Failed to send OTP. Please check your email configuration.")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def verify_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('register')
    
    user = CustomUser.objects.get(id=user_id)
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            otp = OTP.objects.filter(user=user, code=otp_code, is_used=False).last()
            if otp and otp.is_valid():
                user.is_verified = True
                user.save()
                otp.is_used = True
                otp.save()
                login(request, user)
                del request.session['otp_user_id']
                messages.success(request, "Email verified successfully! Welcome to the portal.")
                return redirect('profile')
            else:
                messages.error(request, "Invalid or expired OTP.")
    else:
        form = OTPForm()
    return render(request, 'accounts/verify_otp.html', {'form': form, 'user': user})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                if not user.is_verified:
                    create_and_send_otp(user)
                    request.session['otp_user_id'] = user.id
                    messages.warning(request, "Please verify your email first.")
                    return redirect('verify_otp')
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                if user.is_staff:
                    return redirect('admin_panel:dashboard')
                return redirect('exam_list')
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

def resend_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.error(request, "Session expired. Please register or login again.")
        return redirect('register' if request.path.endswith('register') else 'login')
    
    try:
        user = CustomUser.objects.get(id=user_id)
        if user.is_verified:
            messages.info(request, "Account already verified.")
            return redirect('login')
            
        if create_and_send_otp(user):
            messages.success(request, "A new verification code has been sent to your email.")
        else:
            messages.error(request, "Failed to send new OTP. Please try again later.")
            
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('register')
        
    return redirect('verify_otp')

@login_required
def get_notifications(request):
    notifications = request.user.notifications.all()[:10]
    unread_count = request.user.notifications.filter(is_read=False).count()
    data = {
        'notifications': [
            {
                'id': n.id,
                'message': n.message,
                'link': n.link or '#',
                'is_read': n.is_read,
                'created_at': n.created_at.strftime("%b %d, %H:%M")
            } for n in notifications
        ],
        'unread_count': unread_count
    }
    return JsonResponse(data)

@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
