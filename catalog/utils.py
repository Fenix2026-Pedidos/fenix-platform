"""
Utilidades para el catálogo: traducción automática de productos.
"""
from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)


def translate_text(text: str, source_lang: str = 'es', target_lang: str = 'zh-CN') -> str:
    """
    Traduce texto usando Google Translate (gratuito, sin API key).
    
    Args:
        text: Texto a traducir
        source_lang: Idioma origen (default: 'es')
        target_lang: Idioma destino (default: 'zh-CN' para chino simplificado)
    
    Returns:
        Texto traducido o el texto original si falla la traducción
    """
    if not text or not text.strip():
        return text
    
    try:
        # deep-translator requiere 'zh-CN' para chino simplificado (no 'zh')
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(text)
        return translated
    except Exception as e:
        logger.warning(f"Error al traducir texto: {e}")
        # Si falla, retornar el texto original
        return text


def translate_product_fields(product, translate_name=True, translate_description=True):
    """
    Traduce automáticamente los campos de un producto de español a chino simplificado.
    
    Args:
        product: Instancia del modelo Product
        translate_name: Si True, traduce name_es -> name_zh_hans
        translate_description: Si True, traduce description_es -> description_zh_hans
    
    Returns:
        Dict con los campos traducidos: {'name_zh_hans': ..., 'description_zh_hans': ...}
    """
    translated = {}
    
    if translate_name and product.name_es:
        translated['name_zh_hans'] = translate_text(product.name_es, 'es', 'zh-CN')
    
    if translate_description and product.description_es:
        translated['description_zh_hans'] = translate_text(product.description_es, 'es', 'zh-CN')
    
    return translated
