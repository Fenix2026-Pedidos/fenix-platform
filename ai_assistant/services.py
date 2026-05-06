import logging
from django.conf import settings
from .framework.engine import SynergIAEngine
from .framework.rag import SynergIARAG
from .framework.security import SecurityShield

logger = logging.getLogger(__name__)

class AIService:
    """
    Servicio de IA unificado de Fenix basado en el Framework de Synerg-IA.
    Centraliza el orquestador, el RAG y la seguridad.
    """
    
    _engine = None
    _rag = None

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            api_key = getattr(settings, 'GOOGLE_API_KEY', '')
            cls._engine = SynergIAEngine(api_key)
        return cls._engine

    @classmethod
    def get_rag(cls):
        if cls._rag is None:
            api_key = getattr(settings, 'GOOGLE_API_KEY', '')
            cls._rag = SynergIARAG(api_key)
        return cls._rag

    @staticmethod
    def generate_response(user_query, history=None):
        """
        Genera una respuesta completa usando el framework modular de Synerg-IA.
        """
        # 1. Sanitización de Entrada
        clean_query = SecurityShield.sanitize(user_query)
        
        # 2. Protección contra Prompt Injection
        if SecurityShield.filter_prompt_injection(clean_query):
            logger.warning(f"[Security] Intento de Prompt Injection detectado: {clean_query}")
            return "Lo siento, como asistente estratégico de Fenix, no puedo procesar ese tipo de instrucciones. ¿En qué puedo ayudarte respecto a la plataforma?"

        try:
            # 3. Recuperación de Contexto (RAG)
            rag = AIService.get_rag()
            context = rag.get_relevant_context(clean_query)
            
            # 4. Generación con Failover (Engine)
            engine = AIService.get_engine()
            response_text = engine.ask(
                message=clean_query,
                history=history,
                knowledge_base=context
            )
            
            return response_text
            
        except Exception as e:
            logger.error(f"[AIService] Error crítico: {e}")
            return "Ha habido un problema puntual al procesar la solicitud. Puedes intentarlo de nuevo o reformular tu consulta."
