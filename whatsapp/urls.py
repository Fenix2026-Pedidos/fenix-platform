"""
URLs para la app de WhatsApp
"""
from django.urls import path
from .views import SendWhatsAppMessageView

app_name = 'whatsapp'

urlpatterns = [
    path('api/whatsapp/send/', SendWhatsAppMessageView.as_view(), name='send_message'),
]
