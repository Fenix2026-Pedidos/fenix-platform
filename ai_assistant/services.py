import logging
import google.generativeai as genai
from django.conf import settings
from .models import KnowledgeBase
from pgvector.django import CosineDistance
from .governance import FenixGovernance

logger = logging.getLogger(__name__)

# Configuración de Gemini
if hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
else:
    logger.warning("GOOGLE_API_KEY no configurada en settings.py")

class AIService:
    @staticmethod
    def get_embedding(text):
        """
        Obtiene el vector (embedding) de un texto usando Gemini.
        """
        if not settings.GOOGLE_API_KEY:
            return None
        
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document",
                title="Fenix Knowledge Base"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error al obtener embedding: {e}")
            return None

    @staticmethod
    def search_knowledge(query_text, limit=5):
        """
        Busca los fragmentos de conocimiento más relevantes usando búsqueda vectorial.
        """
        query_embedding = AIService.get_embedding(query_text)
        if not query_embedding:
            return KnowledgeBase.objects.none()

        return KnowledgeBase.objects.annotate(
            distance=CosineDistance('embedding', query_embedding)
        ).order_by('distance')[:limit]

    @staticmethod
    def generate_response(user_query, context_fragments, history=None):
        """
        Genera una respuesta final siguiendo las reglas de gobernanza de Synerg-IA.
        """
        if not settings.GOOGLE_API_KEY:
            return "Lo siento, el servicio de IA no está configurado."

        # 1. Preparar Contexto y Prompt de Gobernanza
        context_text = "\n\n".join([f"Fragmento: {f.content}" for f in context_fragments])
        system_instruction = FenixGovernance.get_system_prompt(context_text)
        
        # 2. Sanear Historia (Google requiere que empiece por user)
        sanitized_history = history or []
        while sanitized_history and sanitized_history[0].get('role') != 'user':
            sanitized_history.pop(0)

        try:
            # 3. Configurar Modelo con Instrucciones del Sistema (Gobernanza)
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=system_instruction
            )
            
            chat = model.start_chat(history=sanitized_history)
            response = chat.send_message(user_query)
            
            return response.text
        except Exception as e:
            logger.error(f"Error al generar respuesta de IA: {e}")
            return "Ha habido un problema puntual al procesar la solicitud. Puedes intentarlo de nuevo o reformular tu consulta."
