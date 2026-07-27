import logging
from email.utils import parseaddr
import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class ResendDeliveryError(RuntimeError):
    """Error de entrega que debe conocer el flujo que solicitó el envío."""


class ResendEmailBackend(BaseEmailBackend):
    @staticmethod
    def _response_error_message(response):
        try:
            payload = response.json()
        except (ValueError, AttributeError):
            detail = (getattr(response, "text", "") or "").strip()
            return detail[:300] or "respuesta no interpretable"
        return payload.get("message") or payload.get("name") or "error no detallado"

    def _fail(self, message, *, cause=None):
        logger.error(message)
        if not self.fail_silently:
            raise ResendDeliveryError(message) from cause

    def send_messages(self, email_messages):
        """
        Envía los mensajes de correo a través de la API REST de Resend mediante HTTPS.
        Esto previene bloqueos de puertos y asegura entregas inmediatas.
        """
        if not email_messages:
            return 0
        
        api_key = getattr(settings, 'RESEND_API_KEY', '')
        if not api_key:
            message = "RESEND_API_KEY no está configurada en los settings de Django."
            if self.fail_silently:
                logger.error(message)
                return 0
            raise ImproperlyConfigured(message)
            
        sent_count = 0
        for message in email_messages:
            try:
                # Determinamos el remitente
                from_email = message.from_email
                from_address = parseaddr(from_email or "")[1].lower()
                # Si el remitente es el de por defecto genérico o de gmail, usamos el verificado de Resend
                if not from_address or from_address == "noreply@fenix.com" or from_address.endswith("@gmail.com"):
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
                            
                response = requests.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Accept": "application/json",
                        "User-Agent": "Fenix-Platform/1.0",
                    },
                    timeout=15,
                )
                if not response.ok:
                    detail = self._response_error_message(response)
                    self._fail(
                        f"Resend rechazó el email (HTTP {response.status_code}): {detail}"
                    )

                logger.info("Email enviado correctamente mediante Resend.")
                sent_count += 1
            except requests.RequestException as e:
                self._fail(
                    f"Error de transporte en Resend: {type(e).__name__}",
                    cause=e,
                )
            except Exception as e:
                if isinstance(e, ResendDeliveryError):
                    raise
                self._fail(
                    f"Error de transporte en Resend: {type(e).__name__}",
                    cause=e,
                )
                
        return sent_count
