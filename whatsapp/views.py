"""
Vistas para la integración de WhatsApp
"""
import json
import logging
from django.http import JsonResponse
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
            
            # 2. Construir mensaje final para WhatsApp
            whatsapp_text = f"Nuevo contacto Fenix:\n\nNombre: {name}\nPágina: {page_url if page_url else 'No especificada'}\n\nMensaje:\n{message}"
            
            # 3. Enviar mensaje a través del servicio
            result = send_whatsapp_message(whatsapp_text)
            
            # 4. Actualizar el Lead con la respuesta
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
                    'message': 'Mensaje enviado correctamente'
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
