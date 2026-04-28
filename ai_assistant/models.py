from django.db import models
from pgvector.django import VectorField

class KnowledgeBase(models.Model):
    """
    Capa de conocimiento para el asistente inteligente.
    Almacena fragmentos de texto y sus representaciones vectoriales (embeddings).
    """
    content = models.TextField(help_text="Contenido de texto del fragmento de conocimiento.")
    metadata = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Información adicional (ej: id_producto, categoría, fuente)."
    )
    # Dimension 3072 es la estándar para el modelo gemini-embedding-001
    embedding = VectorField(dimensions=3072, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Base de Conocimiento"
        verbose_name_plural = "Bases de Conocimiento"
        # Opcional: Índice HNSW para búsquedas vectoriales rápidas en producción
        # indexes = [HnswIndex(name='knowledge_embedding_index', fields=['embedding'])]

    def __str__(self):
        source = self.metadata.get('source', 'General')
        return f"[{source}] {self.content[:50]}..."
