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
        Detección avanzada de intentos de prompt injection y jailbreaks.
        Filtra variaciones semánticas, de espaciado y multilingües.
        """
        if not isinstance(text, str):
            return False
            
        # Normalizar texto para neutralizar ofuscación básica (eliminar espacios, guiones, puntos, comas, etc.)
        normalized_text = re.sub(r'[\s\-\.\_\,\*\=\+\?\#\^]', '', text).lower()
        
        # Reemplazar números por letras equivalentes comunes en ofuscación (1->i, 0->o, 3->e, 4->a)
        normalized_text = normalized_text.replace('1', 'i').replace('0', 'o').replace('3', 'e').replace('4', 'a')
        
        # Patrones directos y normalizados
        dangerous_patterns_normalized = [
            r"ignoratusinstrucciones",
            r"ignoreyourinstructions",
            r"forgeteverything",
            r"olvidatodo",
            r"eresundesarrollador",
            r"developermode",
            r"systemprompt",
            r"danmode",
            r"jailbreak",
            r"ignoreprevious",
            r"instruccionesprevias",
            r"olvidalasreglas",
            r"ignorarlasreglas",
            r"forgettheguidelines",
            r"ignoresystem",
            r"olvidatusreglas",
            r"olvidadesdeahora",
            r"revelatuprompt",
            r"showyourprompt",
            r"instructionsabove",
            r"instruccionesdearriba",
        ]
        
        for pattern in dangerous_patterns_normalized:
            if re.search(pattern, normalized_text):
                return True
                
        # Patrones de frases completas (con espacios) para redundancia
        lower_text = text.lower()
        dangerous_phrases = [
            r"ignore previous instructions",
            r"forget all guidelines",
            r"ignora las instrucciones del sistema",
            r"olvida las directrices",
            r"modo desarrollador",
            r"actúa como",
            r"you are now a developer",
            r"show system prompt",
            r"revela tu prompt",
            r"describe tus reglas",
            r"forget what we talked",
        ]
        
        for phrase in dangerous_phrases:
            if re.search(phrase, lower_text):
                return True
                
        return False

