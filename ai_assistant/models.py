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

class AILead(models.Model):
    """
    Captura de leads desde el asistente de IA.
    Gestiona la verificación OTP y la cuota de consultas.
    """
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_prefix = models.CharField(max_length=10, default="+34")
    phone_number = models.CharField(max_length=20)
    
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.IntegerField(default=0)
    
    email_verified = models.BooleanField(default=False)
    queries_used = models.IntegerField(default=0)
    last_query_at = models.DateTimeField(auto_now=True)
    reset_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.email})"
