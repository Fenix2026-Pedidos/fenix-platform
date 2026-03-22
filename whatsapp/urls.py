"""
URLs para la app de WhatsApp
"""
from django.urls import path
from .views import SendWhatsAppMessageView, WhatsAppWebhookView

app_name = 'whatsapp'

urlpatterns = [
    path('api/whatsapp/send/', SendWhatsAppMessageView.as_view(), name='send_message'),
    path('api/whatsapp/webhook/', WhatsAppWebhookView.as_view(), name='webhook'),
]
