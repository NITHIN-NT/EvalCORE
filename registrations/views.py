from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from exams.models import Exam
from .models import Registration
from .forms import RegistrationForm
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def register_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if not exam.is_registration_open:
        messages.error(request, "Registration for this exam is closed.")
        return redirect('exam_list')
    
    existing_reg = Registration.objects.filter(student=request.user, exam=exam).first()
    if existing_reg and existing_reg.payment_status == 'Success':
        messages.warning(request, "You are already registered and paid for this exam.")
        return redirect('profile')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create or update registration
                    registration, created = Registration.objects.update_or_create(
                        student=request.user,
                        exam=exam,
                        defaults={'document': form.cleaned_data['document']}
                    )
                    
                    # Create Razorpay Order
                    amount = int(exam.fees * 100)  # Amount in paise
                    data = {
                        "amount": amount,
                        "currency": "INR",
                        "receipt": f"reg_{registration.id}",
                    }
                    order = client.order.create(data=data)
                    
                    registration.razorpay_order_id = order['id']
                    registration.save()
                    
                    return render(request, 'registrations/payment.html', {
                        'registration': registration,
                        'order': order,
                        'razorpay_key': settings.RAZORPAY_KEY_ID,
                        'exam': exam
                    })
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
    else:
        form = RegistrationForm()
    
    return render(request, 'registrations/register_form.html', {'form': form, 'exam': exam})

@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            # Verify signature
            client.utility.verify_payment_signature(params_dict)
            
            registration = Registration.objects.get(razorpay_order_id=order_id)
            registration.payment_status = 'Success'
            registration.razorpay_payment_id = payment_id
            registration.razorpay_signature = signature
            registration.save()
            
            messages.success(request, "Payment successful! Your registration is confirmed.")
            return redirect('registrations:payment_success', registration_id=registration.id)
            
        except Exception as e:
            messages.error(request, f"Payment verification failed: {e}")
            # Try to find registration by order_id or fallback to registration_id from GET
            order_id = request.POST.get('razorpay_order_id', '')
            registration_id = request.GET.get('registration_id')
            
            registration = None
            if order_id and order_id.strip():
                registration = Registration.objects.filter(razorpay_order_id=order_id).first()
            
            if not registration and registration_id:
                registration = Registration.objects.filter(id=registration_id).first()
            
            if registration:
                return redirect('registrations:payment_failure', registration_id=registration.id)
                
            return redirect('exam_list')
    return redirect('exam_list')

@login_required
def payment_success(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id, student=request.user)
    return render(request, 'registrations/payment_success.html', {'registration': registration})

@login_required
def payment_failure(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id, student=request.user)
    return render(request, 'registrations/payment_failure.html', {'registration': registration})

@login_required
def view_hall_ticket(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    
    # Security check: Only the student or staff can view
    if not request.user.is_staff and registration.student != request.user:
        messages.error(request, "Access denied.")
        return redirect('profile')
    
    if registration.status != 'Approved':
        messages.error(request, "Hall ticket is only available for approved registrations.")
        return redirect('profile')
    
    # Generate QR code data (same logic as email)
    from .utils import generate_qr_code_bytes
    import base64
    
    qr_data = f"Reg No: {registration.registration_number}\nStudent: {registration.student.get_full_name()}\nExam: {registration.exam.name}\nDate: {registration.exam.exam_date}\nLocation: {registration.exam.location}"
    qr_bytes = generate_qr_code_bytes(qr_data)
    qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
    
    context = {
        'registration': registration,
        'user': registration.student,
        'exam': registration.exam,
        'qr_code': qr_base64,
    }
    
    return render(request, 'registrations/printable_hall_ticket.html', context)

