import re
from django.utils.html import escape

class SecurityShield:
    """
    SYNERG-IA SECURITY SHIELD (Módulo de Gobernanza v1.0)
    Centraliza la seguridad del framework para asegurar que cada interacción sea limpia y segura.
    """
    
    @staticmethod
    def sanitize(text):
        """
        Sanitiza strings para prevenir XSS e inyecciones básicas.
        """
        if not isinstance(text, str):
            return text
        
        # Escapado HTML estándar
        text = escape(text)
        
        # Eliminar caracteres potencialmente peligrosos extra
        text = text.strip()
        return text

    @staticmethod
    def validate_gdpr(accepted):
        """
        Validador de cumplimiento RGPD.
        """
        if not accepted:
            raise ValueError("El consentimiento de privacidad es obligatorio bajo RGPD.")
        return True

    @staticmethod
    def filter_prompt_injection(text):
        """
        Detección básica de intentos de prompt injection.
        """
        dangerous_patterns = [
            r"ignora tus instrucciones",
            r"ignore your instructions",
            r"forget everything",
            r"olvida todo",
            r"eres un desarrollador",
            r"developer mode",
            r"system prompt",
        ]
        
        lower_text = text.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, lower_text):
                return True
        return False
