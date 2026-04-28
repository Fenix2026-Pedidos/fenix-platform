from django.contrib import admin
from .models import KnowledgeBase
from .services import AIService

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('content_summary', 'source_tag', 'has_embedding', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'metadata')
    readonly_fields = ('embedding', 'created_at', 'updated_at')
    
    actions = ['generate_embeddings_action']

    def content_summary(self, obj):
        return obj.content[:75] + "..." if len(obj.content) > 75 else obj.content
    content_summary.short_description = "Contenido"

    def source_tag(self, obj):
        return obj.metadata.get('source', 'General')
    source_tag.short_description = "Fuente"

    def has_embedding(self, obj):
        return obj.embedding is not None
    has_embedding.boolean = True
    has_embedding.short_description = "Vect."

    def generate_embeddings_action(self, request, queryset):
        """Acción masiva para generar embeddings."""
        count = 0
        for item in queryset:
            embedding = AIService.get_embedding(item.content)
            if embedding:
                item.embedding = embedding
                item.save()
                count += 1
        self.message_user(request, f"Se han generado embeddings para {count} registros.")
    generate_embeddings_action.short_description = "Generar Embeddings para los seleccionados"

    def save_model(self, request, obj, form, change):
        """Sobrescribir para generar embedding automáticamente al guardar si el contenido cambia."""
        if not obj.embedding or 'content' in form.changed_data:
            embedding = AIService.get_embedding(obj.content)
            if embedding:
                obj.embedding = embedding
        super().save_model(request, obj, form, change)
