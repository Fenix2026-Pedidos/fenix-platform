import logging
from .models_bridge import get_knowledge_base_model, get_cosine_distance
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

class SynergIARAG:
    """
    AI Framework Synerg-IA: Professional RAG Manager
    Gestiona la recuperación semántica usando la base de datos de Fenix.
    """
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.threshold = 0.65  # Umbral mínimo de relevancia
        self.top_k = 3         # Mejores fragmentos
        
        if api_key:
            genai.configure(api_key=api_key)

    def get_embedding(self, text):
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"[RAG] Error al obtener embedding: {e}")
            return None

    def get_relevant_context(self, query):
        """
        Recupera el contexto relevante de la base de datos de Fenix.
        """
        try:
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                return ""

            KnowledgeBase = get_knowledge_base_model()
            CosineDistance = get_cosine_distance()

            # Búsqueda vectorial usando pgvector
            results = KnowledgeBase.objects.annotate(
                distance=CosineDistance('embedding', query_embedding)
            ).filter(distance__lte=(1 - self.threshold)).order_by('distance')[:self.top_k]

            if not results:
                logger.info(f"[RAG] No se encontró contexto relevante para: {query}")
                return ""

            context_header = "\n\n--- INFORMACIÓN ESTRATÉGICA RECUPERADA ---\n"
            context_body = "\n\n".join([f"[RELEVANCIA: {round((1-r.distance)*100, 1)}%] {r.content}" for r in results])
            
            return f"{context_header}{context_body}\n--- FIN DE INFORMACIÓN ADICIONAL ---\n"
            
        except Exception as e:
            logger.error(f"[RAG] Error en la recuperación: {e}")
            return ""
