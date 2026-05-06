import requests
import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)

class CRMService:
    """
    Servicio de sincronización con el CRM de Fenix (Google Sheets).
    """
    
    @staticmethod
    def sync_lead(data):
        """
        Envía los datos del lead al Webhook de Google Sheets de Fenix.
        """
        webhook_url = getattr(settings, 'GOOGLE_SHEETS_WEBHOOK_URL', None)
        
        if not webhook_url:
            logger.warning("[CRM] GOOGLE_SHEETS_WEBHOOK_URL no configurada. Sincronización omitida.")
            return False

        try:
            # Asegurar que enviamos los campos que el script espera
            payload = {
                "source": data.get("source", "Fenix Assistant"),
                "name": data.get("name"),
                "email": data.get("email"),
                "phone_prefix": data.get("phone_prefix", ""),
                "phone_number": data.get("phone_number", ""),
                "company": data.get("company", "-"),
                "message": data.get("message", "Solicitud desde el asistente")
            }
            
            response = requests.post(
                webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"[CRM] Lead sincronizado con éxito para: {payload['email']}")
                return True
            else:
                logger.error(f"[CRM] Error en la respuesta del Webhook ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"[CRM] Excepción al sincronizar lead: {e}")
            return False
