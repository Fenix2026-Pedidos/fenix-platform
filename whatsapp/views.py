"""Endpoints de WhatsApp con autenticación, minimización y control de abuso."""

import hashlib
import hmac
import json
import logging
import os
from urllib.parse import quote

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from core.rate_limit import rate_limited
from .models import WhatsAppLead
from .services import send_whatsapp_message

logger = logging.getLogger(__name__)


class SendWhatsAppMessageView(View):
    """Envío desde páginas propias; conserva protección CSRF."""

    def post(self, request):
        if rate_limited(request, 'whatsapp-send', 3, 15 * 60):
            return JsonResponse({'success': False, 'error': 'Demasiadas solicitudes'}, status=429)
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

        name = str(data.get('name', '')).strip()[:100]
        message = str(data.get('message', '')).strip()[:2000]
        page_url = str(data.get('page_url', '')).strip()[:500]
        if not name or not message:
            return JsonResponse({'success': False, 'error': 'Nombre y mensaje son obligatorios'}, status=400)

        lead = WhatsAppLead.objects.create(name=name, message=message, page_url=page_url)
        try:
            from crm.models import CRMLead
            from crm.services import CRMLeadService
            CRMLeadService.log_lead(
                channel=CRMLead.CHANNEL_WHATSAPP,
                full_name=name,
                message=message,
                source='Formulario de WhatsApp Web',
            )
        except Exception:
            logger.exception('No se pudo registrar el lead de WhatsApp en CRM')

        whatsapp_text = f'Nuevo contacto Fenix:\n\nNombre: {name}\n\nMensaje:\n{message}'
        result = send_whatsapp_message(whatsapp_text)
        lead.sent_successfully = bool(result.get('success'))
        # No persistir respuestas completas del proveedor, que pueden contener PII.
        lead.api_response = {'status': 'sent' if lead.sent_successfully else 'failed'}
        lead.save(update_fields=['sent_successfully', 'api_response'])

        if not lead.sent_successfully:
            logger.error('Falló el envío de WhatsApp; lead_id=%s', lead.pk)
            return JsonResponse({'success': False, 'error': 'No se pudo enviar el mensaje'}, status=502)

        target = os.getenv('DEFAULT_WHATSAPP_TARGET', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        mobile = any(value in user_agent for value in ('iphone', 'android', 'ipad', 'mobile', 'tablet'))
        base = 'https://wa.me/' if mobile else 'https://web.whatsapp.com/send?phone='
        separator = '?text=' if mobile else '&text='
        return JsonResponse({
            'success': True,
            'message': 'Mensaje enviado correctamente',
            'whatsapp_url': f'{base}{target}{separator}{quote(whatsapp_text)}',
        })


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """Webhook externo de Meta; CSRF no aplica, se valida firma HMAC."""

    def get(self, request):
        mode = request.GET.get('hub.mode', '')
        token = request.GET.get('hub.verify_token', '')
        challenge = request.GET.get('hub.challenge', '')
        expected = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', '')
        if expected and mode == 'subscribe' and hmac.compare_digest(token, expected):
            return HttpResponse(challenge, status=200)
        logger.warning('Falló la verificación inicial del webhook de WhatsApp')
        return HttpResponse('Forbidden', status=403)

    def post(self, request):
        app_secret = os.getenv('WHATSAPP_APP_SECRET', '')
        supplied = request.META.get('HTTP_X_HUB_SIGNATURE_256', '')
        if not app_secret or not supplied.startswith('sha256='):
            return HttpResponse('Forbidden', status=403)
        expected = 'sha256=' + hmac.new(
            app_secret.encode('utf-8'), request.body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(supplied, expected):
            logger.warning('Firma incorrecta en webhook de WhatsApp')
            return HttpResponse('Forbidden', status=403)

        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return HttpResponse('Invalid JSON', status=400)

        processed = 0
        try:
            from crm.models import CRMLead
            from crm.services import CRMLeadService
            for entry in body.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    names = {
                        c.get('wa_id'): c.get('profile', {}).get('name')
                        for c in value.get('contacts', []) if c.get('wa_id')
                    }
                    for msg in value.get('messages', []):
                        sender = str(msg.get('from', ''))[:30]
                        msg_type = msg.get('type', '')
                        if msg_type == 'text':
                            text = msg.get('text', {}).get('body', '')
                        elif msg_type == 'button':
                            text = msg.get('button', {}).get('text', '')
                        else:
                            text = f'[{msg_type or "unknown"}]'
                        text = str(text).strip()[:4000]
                        if sender and text:
                            CRMLeadService.log_lead(
                                channel=CRMLead.CHANNEL_WHATSAPP,
                                full_name=str(names.get(sender) or 'Contacto WhatsApp')[:255],
                                phone=sender,
                                message=text,
                                source='WhatsApp Incoming Webhook',
                                metadata={'message_id': msg.get('id'), 'type': msg_type},
                            )
                            processed += 1
        except Exception:
            logger.exception('Error procesando webhook autenticado de WhatsApp')
            return HttpResponse('Internal Server Error', status=500)

        logger.info('Webhook de WhatsApp procesado; mensajes=%s', processed)
        return HttpResponse('EVENT_RECEIVED', status=200)
