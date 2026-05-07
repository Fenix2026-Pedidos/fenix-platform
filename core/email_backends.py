import json
import urllib.request
import urllib.error
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)

class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        """
        Envía los mensajes de correo a través de la API REST de Resend mediante HTTPS.
        Esto previene bloqueos de puertos y asegura entregas inmediatas.
        """
        if not email_messages:
            return 0
        
        api_key = getattr(settings, 'RESEND_API_KEY', '')
        if not api_key:
            logger.error("RESEND_API_KEY no está configurada en los settings de Django.")
            print("--- [ERROR RESEND] RESEND_API_KEY no configurada ---")
            return 0
            
        sent_count = 0
        for message in email_messages:
            try:
                # Determinamos el remitente
                from_email = message.from_email
                # Si el remitente es el de por defecto genérico o de gmail, usamos el verificado de Resend
                if not from_email or "noreply@fenix.com" in from_email or "plataformafenix2026@gmail.com" in from_email:
                    from_email = getattr(settings, 'RESEND_DEFAULT_FROM', 'onboarding@resend.dev')
                
                recipients = message.to
                if not isinstance(recipients, (list, tuple)):
                    recipients = [recipients]

                payload = {
                    "from": from_email,
                    "to": list(recipients),
                    "subject": message.subject,
                    "text": message.body,
                }
                
                # Extraemos el contenido HTML si está presente (para EmailMultiAlternatives)
                if hasattr(message, 'alternatives') and message.alternatives:
                    for alt in message.alternatives:
                        if alt[1] == 'text/html':
                            payload['html'] = alt[0]
                            break
                elif hasattr(message, 'content_subtype') and message.content_subtype == 'html':
                    payload['html'] = message.body
                            
                req = urllib.request.Request(
                    "https://api.resend.com/emails",
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )
                
                with urllib.request.urlopen(req) as response:
                    res_body = response.read().decode('utf-8')
                    logger.info(f"Email enviado con éxito mediante Resend: {res_body}")
                    print(f"--- [ÉXITO RESEND] Email enviado: {res_body} ---")
                    sent_count += 1
            except urllib.error.HTTPError as e:
                err_content = e.read().decode('utf-8')
                logger.error(f"Error HTTP en Resend ({e.code}): {err_content}")
                print(f"--- [ERROR RESEND API] HTTP {e.code}: {err_content} ---")
            except Exception as e:
                logger.error(f"Error general en Resend Backend: {e}")
                print(f"--- [ERROR RESEND] General: {e} ---")
                
        return sent_count
