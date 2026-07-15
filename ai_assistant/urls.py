from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('session-status/', views.session_status, name='session_status'),
    path('chat/', views.assistant_chat, name='chat'),
    path('capture-lead/', views.capture_lead, name='capture_lead'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
]
