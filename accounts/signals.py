from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from .models import CustomUser, Notification

@receiver(post_save, sender=SocialAccount)
def verify_social_user(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        if not user.is_verified:
            user.is_verified = True
            user.save()

@receiver(post_save, sender='exams.Exam')
def notify_new_exam(sender, instance, created, **kwargs):
    if created:
        students = CustomUser.objects.filter(is_staff=False)
        for student in students:
            Notification.objects.create(
                user=student,
                message=f"A new exam has been added: {instance.name}",
                link="/exams/"
            )

@receiver(post_save, sender='registrations.Registration')
def notify_registration_status_change(sender, instance, created, **kwargs):
    if not created:
        Notification.objects.create(
            user=instance.student,
            message=f"Update on your {instance.exam.name} registration: Status is now {instance.status}.",
            link="/accounts/profile/"
        )
