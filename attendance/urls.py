from django.urls import path
from . import views

# app_name = 'attendance'

urlpatterns = [
    # Teacher URLs
    path('',views.home, name="home"),
    path('readme',views.readme, name="readme"),
    path('dashboard', views.teacher_dashboard, name='teacher_dashboard'),
    path('session/new/', views.create_session, name='create_session'),
    path('session/<uuid:session_id>/', views.session_details, name='session_details'),
    path('session/<uuid:session_id>/toggle-checkout/', views.toggle_checkout, name='toggle_checkout'),
    path('api/session/<uuid:session_id>/live/', views.get_live_attendance, name='get_live_attendance'),
    path('session/<uuid:session_id>/download/', views.download_attendance_csv, name='download_attendance_csv'),

    # Student URLs
    path('attend/<uuid:session_id>/', views.student_form, name='student_form'),
]