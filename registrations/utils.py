import qrcode
import io
import base64
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import random
import string
from email.mime.image import MIMEImage

def generate_registration_number(registration):
    """Generates a unique registration number like REG-2026-XXXX."""
    if registration.registration_number:
        return registration.registration_number
    
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    reg_num = f"REG-{registration.exam.exam_date.year}-{random_str}"
    
    # Simple check for uniqueness (very unlikely to collision with 4 random chars for 1 user, but good practice)
    from .models import Registration
    while Registration.objects.filter(registration_number=reg_num).exists():
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        reg_num = f"REG-{registration.exam.exam_date.year}-{random_str}"
    
    return reg_num

def generate_qr_code_bytes(data):
    """Generates a QR code and returns it as bytes."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

def send_status_email(registration, status, reason=None):
    """Sends an email notification based on the registration status."""
    subject = f"Your Registration for {registration.exam.name} - Status Update"
    
    context = {
        'registration': registration,
        'user': registration.student,
        'exam': registration.exam,
        'status': status,
        'reason': reason,
    }
    
    if status == 'Approved':
        subject = f"Hall Ticket: Registration Approved for {registration.exam.name}"
        # Generate Hall Ticket Specific Details
        if not registration.registration_number:
            registration.registration_number = generate_registration_number(registration)
            registration.save()
        
        qr_data = f"Reg No: {registration.registration_number}\nStudent: {registration.student.get_full_name()}\nExam: {registration.exam.name}\nDate: {registration.exam.exam_date}\nLocation: {registration.exam.location}"
        context['qr_bytes'] = generate_qr_code_bytes(qr_data)
        template = 'emails/hall_ticket.html'
    elif status == 'Rejected':
        template = 'emails/rejection_email.html'
    elif status == 'Hold':
        template = 'emails/hold_email.html'
    else:
        return # No email for undefined statuses
    
    html_content = render_to_string(template, context)
    text_content = strip_tags(html_content)
    
    email_from = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    msg = EmailMultiAlternatives(subject, text_content, email_from, [registration.student.email])
    msg.attach_alternative(html_content, "text/html")
    
    if status == 'Approved' and 'qr_bytes' in context:
        img = MIMEImage(context['qr_bytes'])
        img.add_header('Content-ID', '<qr_code>')
        img.add_header('Content-Disposition', 'inline', filename='qr_code.png')
        msg.attach(img)
        
    msg.send()
