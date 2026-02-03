"""
Servicio para enviar mensajes a través de WhatsApp Business Cloud API (Meta)
"""
import os
import logging
import requests
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
DEFAULT_WHATSAPP_TARGET = os.getenv('DEFAULT_WHATSAPP_TARGET', '')

# URL base de la API de WhatsApp Cloud
WHATSAPP_API_BASE_URL = 'https://graph.facebook.com/v18.0'


def send_whatsapp_message(text: str, recipient: Optional[str] = None) -> Dict[str, any]:
    """
    Envía un mensaje de texto a través de WhatsApp Business Cloud API.
    
    Args:
        text: Texto del mensaje a enviar
        recipient: Número de teléfono destino (formato internacional sin +). 
                   Si no se proporciona, usa DEFAULT_WHATSAPP_TARGET
    
    Returns:
        Dict con 'success' (bool) y 'message' (str) o 'error' (str)
    """
    # Validar configuración
    if not WHATSAPP_PHONE_NUMBER_ID:
        error_msg = "WHATSAPP_PHONE_NUMBER_ID no configurado"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    
    if not WHATSAPP_ACCESS_TOKEN:
        error_msg = "WHATSAPP_ACCESS_TOKEN no configurado"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    
    # Usar destinatario por defecto si no se proporciona
    target = recipient or DEFAULT_WHATSAPP_TARGET
    if not target:
        error_msg = "DEFAULT_WHATSAPP_TARGET no configurado y no se proporcionó recipient"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    
    # Validar que el texto no esté vacío
    if not text or not text.strip():
        error_msg = "El mensaje no puede estar vacío"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    
    # Construir URL del endpoint
    url = f"{WHATSAPP_API_BASE_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    # Headers
    headers = {
        'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json',
    }
    
    # Payload según documentación de WhatsApp Cloud API
    payload = {
        "messaging_product": "whatsapp",
        "to": target,
        "type": "text",
        "text": {
            "body": text
        }
    }
    
    try:
        # Enviar request con timeout
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10  # 10 segundos de timeout
        )
        
        # Verificar respuesta
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Mensaje WhatsApp enviado exitosamente a {target}")
            return {
                'success': True,
                'message': 'Mensaje enviado correctamente',
                'whatsapp_response': response_data
            }
        else:
            error_msg = f"Error al enviar mensaje: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': f'Error al enviar mensaje (código {response.status_code})',
                'details': response.text
            }
    
    except requests.exceptions.Timeout:
        error_msg = "Timeout al conectar con WhatsApp API"
        logger.error(error_msg)
        return {'success': False, 'error': 'Timeout al enviar mensaje'}
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'error': 'Error de conexión con WhatsApp API'}
    
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {'success': False, 'error': 'Error inesperado al enviar mensaje'}
