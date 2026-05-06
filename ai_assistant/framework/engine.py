import logging
import google.generativeai as genai
from django.conf import settings
from .governance import SynergIAGovernance

logger = logging.getLogger(__name__)

class SynergIAEngine:
    """
    AI Framework Synerg-IA: Engine
    Gestiona la conectividad con LLMs y el sistema de resiliencia (Failover).
    """
    
    def __init__(self, api_key):
        self.api_key = api_key
        # Configuración de modelos (v1beta para soporte de system_instruction nativo)
        self.primary_model_name = "gemini-2.5-pro"
        self.fallback_model_name = "gemini-2.5-flash"
        
        if api_key:
            genai.configure(api_key=api_key)
        else:
            logger.error("[Framework] GOOGLE_API_KEY no detectada.")

        # Configuramos los Guardrails de Seguridad a nivel de API
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

    def _get_response(self, model_name, message, history, system_instruction):
        """
        Intento de obtención de respuesta para un modelo específico.
        """
        logger.info(f"[Framework] Intentando con: {model_name}...")
        
        model = genai.GenerativeModel(
            model_name=model_name,
            safety_settings=self.safety_settings,
            system_instruction=system_instruction
        )
        
        chat = model.start_chat(history=history)
        response = chat.send_message(message)
        return response.text

    def ask(self, message, history=None, knowledge_base="", is_authenticated=False):
        """
        Método principal con lógica de Failover.
        """
        # 1. Preparar instrucciones del sistema (Gobernanza)
        system_instruction = SynergIAGovernance.get_system_prompt(knowledge_base, is_authenticated=is_authenticated)
        
        # 2. Limpiar historia: Google exige que el primer mensaje sea siempre del 'user'
        sanitized_history = history or []
        while sanitized_history and sanitized_history[0].get('role') != 'user':
            sanitized_history.pop(0)

        try:
            # Intento primario (Máxima Calidad)
            return self._get_response(self.primary_model_name, message, sanitized_history, system_instruction)
        except Exception as e:
            logger.warning(f"[Framework] Error en modelo primario ({self.primary_model_name}): {e}. Activando Failover...")
            try:
                # Intento de respaldo (Máxima Disponibilidad)
                return self._get_response(self.fallback_model_name, message, sanitized_history, system_instruction)
            except Exception as e2:
                logger.error(f"[Framework] Fallo crítico en ambos modelos: {e2}")
                raise e2
