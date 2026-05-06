def get_knowledge_base_model():
    from ai_assistant.models import KnowledgeBase
    return KnowledgeBase

def get_cosine_distance():
    from pgvector.django import CosineDistance
    return CosineDistance
