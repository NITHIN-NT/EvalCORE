from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from exams.models import Exam
import datetime

class ExamSchedulingTest(TestCase):
    def setUp(self):
        self.exam = Exam.objects.create(
            name="Test Exam",
            banner="test_banner.jpg",
            description="Initial Description",
            eligibility="All students",
            exam_date=timezone.now() + datetime.timedelta(days=15),
            is_registration_open=True
        )

    def test_reschedule_more_than_10_days_away(self):
        # Update more than 10 days away should pass
        new_date = self.exam.exam_date + datetime.timedelta(days=1)
        self.exam.exam_date = new_date
        self.exam.save()
        self.assertEqual(self.exam.exam_date, new_date)

    def test_reschedule_less_than_10_days_away(self):
        # Move exam to 5 days from now
        self.exam.exam_date = timezone.now() + datetime.timedelta(days=5)
        self.exam.save()
        
        # Now try to change it again (should fail because it's < 10 days away)
        self.exam.exam_date = timezone.now() + datetime.timedelta(days=6)
        with self.assertRaises(ValidationError):
            self.exam.save()

class OTPTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="test@example.com", password="password")

    def test_otp_generation(self):
        from accounts.models import OTP
        otp = OTP.objects.create(user=self.user, code="123456")
        self.assertTrue(otp.is_valid())
        
        # Test usage
        otp.is_used = True
        otp.save()
        self.assertFalse(otp.is_valid())
