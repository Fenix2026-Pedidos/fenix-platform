"""
Vistas para la integración de WhatsApp
"""
import json
import logging
import os
from urllib.parse import quote
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from .services import send_whatsapp_message
from .models import WhatsAppLead

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SendWhatsAppMessageView(View):
    """
    Endpoint para enviar mensajes de WhatsApp desde el frontend público.
    """
    
    def post(self, request):
        """
        Recibe un POST con:
        {
            "name": "Nombre del usuario",
            "message": "Mensaje del usuario",
            "page_url": "URL de la página desde donde se envió"
        }
        """
        try:
            # Parsear JSON del body
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'JSON inválido'
                }, status=400)
            
            # Validar campos requeridos
            name = data.get('name', '').strip()
            message = data.get('message', '').strip()
            page_url = data.get('page_url', '').strip()
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'error': 'El nombre es requerido'
                }, status=400)
            
            if not message:
                return JsonResponse({
                    'success': False,
                    'error': 'El mensaje es requerido'
                }, status=400)
            
            # 1. Crear el registro del Lead (vía persistencia)
            lead = WhatsAppLead.objects.create(
                name=name,
                message=message,
                page_url=page_url
            )
            
            # Sincronizar con el CRM Omnicanal Unificado
            try:
                from crm.services import CRMLeadService
                from crm.models import CRMLead
                CRMLeadService.log_lead(
                    channel=CRMLead.CHANNEL_WHATSAPP,
                    full_name=name,
                    message=message,
                    source=f"Formulario de WhatsApp Web ({page_url or 'Sin URL'})"
                )
            except Exception as crm_err:
                logger.warning(f"[CRM] Error registrando lead desde SendWhatsAppMessageView: {crm_err}")
            
            # 2. Construir mensaje final para WhatsApp
            whatsapp_text = f"Nuevo contacto Fenix:\n\nNombre: {name}\nPágina: {page_url if page_url else 'No especificada'}\n\nMensaje:\n{message}"
            
            # 3. Enviar mensaje a través del servicio
            result = send_whatsapp_message(whatsapp_text)
            
            # 4. Determinar URL según dispositivo (Web vs Móvil/Tablet)
            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            is_mobile = any(dev in user_agent for dev in ['iphone', 'android', 'ipad', 'mobile', 'tablet'])
            whatsapp_phone = os.getenv('DEFAULT_WHATSAPP_TARGET', '')
            
            if is_mobile:
                # wa.me es universal y abre la app en móviles/tablets
                whatsapp_url = f"https://wa.me/{whatsapp_phone}?text={quote(whatsapp_text)}"
            else:
                # Forzar WhatsApp Web en Desktop según requerimiento
                whatsapp_url = f"https://web.whatsapp.com/send?phone={whatsapp_phone}&text={quote(whatsapp_text)}"

            # 5. Actualizar el Lead con la respuesta
            lead.sent_successfully = result['success']
            lead.api_response = result.get('whatsapp_response')
            if not result['success']:
                # Guardar el error en api_response para debugging si falla
                lead.api_response = {'error': result.get('error'), 'details': result.get('details')}
            lead.save()
            
            if result['success']:
                logger.info(f"Mensaje WhatsApp enviado y guardado (Lead ID: {lead.id})")
                return JsonResponse({
                    'success': True,
                    'message': 'Mensaje enviado correctamente',
                    'whatsapp_url': whatsapp_url
                })
            else:
                logger.error(f"Error al enviar mensaje WhatsApp: {result.get('error', 'Error desconocido')}")
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Error al enviar mensaje')
                }, status=500)
        
        except Exception as e:
            logger.error(f"Error inesperado en SendWhatsAppMessageView: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """
    Endpoint para recibir webhooks de WhatsApp API.
    """
    
    def get(self, request):
        """
        Verificación del webhook requerida por Meta.
        """
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        verify_token_env = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'fenix_seguridad_webhook_2026')
        
        if mode and token:
            if mode == 'subscribe' and token == verify_token_env:
                logger.info("Webhook verificado correctamente por Meta")
                return HttpResponse(challenge, status=200)
            else:
                logger.warning(f"Fallo en verificación de Webhook. Token recibido: {token}")
                return HttpResponse('Error de verificación', status=403)
                
        return HttpResponse('Bad Request', status=400)
        
    def post(self, request):
        """
        Recepción de mensajes y notificaciones de estado.
        """
        try:
            body = json.loads(request.body)
            # Loggear payload para ver la estructura recibida de Meta
            logger.info(f"\n[WHATSAPP WEBHOOK] Evento entrante:\n{json.dumps(body, indent=2)}\n")
            
            # PARSEO DEL BODY DE WHATSAPP WEBHOOK (META CLOUD API)
            entries = body.get('entry', [])
            for entry in entries:
                changes = entry.get('changes', [])
                for change in changes:
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    contacts = value.get('contacts', [])
                    
                    # Mapear nombres de contacto por su wa_id
                    contact_names = {}
                    for contact in contacts:
                        wa_id = contact.get('wa_id')
                        profile = contact.get('profile', {})
                        name = profile.get('name')
                        if wa_id and name:
                            contact_names[wa_id] = name
                    
                    for msg in messages:
                        sender_phone = msg.get('from')  # Número de teléfono del emisor
                        msg_type = msg.get('type')
                        
                        # Extraer el cuerpo del mensaje de texto
                        msg_body = ""
                        if msg_type == 'text':
                            msg_body = msg.get('text', {}).get('body', '').strip()
                        elif msg_type == 'button':
                            msg_body = msg.get('button', {}).get('text', '').strip()
                        elif msg_type == 'interactive':
                            interactive = msg.get('interactive', {})
                            if interactive.get('type') == 'button_reply':
                                msg_body = interactive.get('button_reply', {}).get('title', '').strip()
                            elif interactive.get('type') == 'list_reply':
                                msg_body = interactive.get('list_reply', {}).get('title', '').strip()
                        else:
                            msg_body = f"[{msg_type.upper()}] Mensaje multimedia o interactivo recibido."

                        if sender_phone and msg_body:
                            # Obtener el nombre del perfil de WhatsApp, o fallback por defecto
                            sender_name = contact_names.get(sender_phone, f"WhatsApp {sender_phone}")
                            
                            # Registrar/actualizar lead e historial en el CRM
                            from crm.services import CRMLeadService
                            from crm.models import CRMLead
                            
                            CRMLeadService.log_lead(
                                channel=CRMLead.CHANNEL_WHATSAPP,
                                full_name=sender_name,
                                phone=sender_phone,
                                message=msg_body,
                                source="WhatsApp Incoming Webhook",
                                metadata=msg
                            )
            
            return HttpResponse('EVENT_RECEIVED', status=200)
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON', status=400)
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}", exc_info=True)
            return HttpResponse('Internal Server Error', status=500)
