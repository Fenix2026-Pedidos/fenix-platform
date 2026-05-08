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
    def generate_response(user_query, history=None, is_authenticated=False, user=None):
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
            
            # Inyectar dinámicamente el Menú Inteligente del Catálogo real de la BBDD
            from .catalog_menu import build_smart_menu_prompt
            smart_menu_prompt = build_smart_menu_prompt()
            context = smart_menu_prompt + "\n" + context
            
            # Si el cliente está autenticado, inyectar dinámicamente sus datos en el contexto de conocimiento
            if is_authenticated and user:
                user_role_display = user.get_role_display() if hasattr(user, 'get_role_display') else getattr(user, 'role', 'user')
                user_info_block = f"""
INFORMACIÓN DEL CLIENTE ACTUAL AUTENTICADO:
- ID de Usuario: {user.id}
- Nombre Completo: {user.display_name if hasattr(user, 'display_name') else user.full_name}
- Email: {user.email}
- Teléfono: {user.phone or getattr(user, 'telefono_reparto', '') or 'No especificado'}
- Empresa/Negocio: {user.company or 'No especificada'}
- Rol/Perfil de Acceso: {user_role_display}
- Estado del Perfil Operativo (Requerido para pedidos): {"Completado" if getattr(user, 'profile_completed', False) else "Incompleto"}
"""
                context = user_info_block + "\n" + context
            
            # 4. Generación con Failover (Engine)
            engine = AIService.get_engine()
            response_text = engine.ask(
                message=clean_query,
                history=history,
                knowledge_base=context,
                is_authenticated=is_authenticated
            )
            
            return response_text
            
        except Exception as e:
            logger.error(f"[AIService] Error crítico: {e}")
            return "Ha habido un problema puntual al procesar la solicitud. Puedes intentarlo de nuevo o reformular tu consulta."
