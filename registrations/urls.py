from django.urls import path
from . import views

app_name = 'registrations'

urlpatterns = [
    path('exam/<int:exam_id>/register/', views.register_exam, name='register_exam'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/success/<int:registration_id>/', views.payment_success, name='payment_success'),
    path('payment/failure/<int:registration_id>/', views.payment_failure, name='payment_failure'),
    path('hall-ticket/<int:registration_id>/', views.view_hall_ticket, name='view_hall_ticket'),
]
