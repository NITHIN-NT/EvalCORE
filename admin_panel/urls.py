from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_login_view, name='login'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('registration/<int:reg_id>/status/<str:status>/', views.update_registration_status, name='update_registration_status'),
    path('registration/<int:reg_id>/delete/', views.delete_registration, name='delete_registration'),
    path('registration/<int:reg_id>/view/', views.registration_detail, name='registration_detail'),
    path('profile/', views.admin_profile, name='profile'),
    
    path('exams/', views.admin_exam_list, name='exam_list'),
    path('exams/create/', views.exam_create, name='exam_create'),
    path('exams/<int:pk>/update/', views.exam_update, name='exam_update'),
    path('exams/<int:pk>/delete/', views.exam_delete, name='exam_delete'),
    path('exams/<int:exam_id>/registrations/', views.exam_registrations, name='exam_registrations'),
    path('exams/<int:exam_id>/bulk-update/<str:status>/', views.bulk_update_registrations, name='bulk_update_registrations'),
]
