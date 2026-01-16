import random
import string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import OTP

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(user, otp_code):
    subject = 'Your Student Portal OTP'
    context = {
        'user': user,
        'otp_code': otp_code,
        'expiry_minutes': settings.OTP_EXPIRY_MINUTES
    }
    
    # Render HTML and plain text versions
    html_content = render_to_string('emails/otp_email.html', context)
    text_content = strip_tags(html_content)
    
    email_from = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    
    msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def create_and_send_otp(user):
    otp_code = generate_otp()
    OTP.objects.create(user=user, code=otp_code)
    try:
        send_otp_email(user, otp_code)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
