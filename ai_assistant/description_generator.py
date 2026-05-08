import os
import logging
import mimetypes
import requests
import google.generativeai as genai
from django.conf import settings
from catalog.utils import translate_text

logger = logging.getLogger(__name__)

class DescriptionGenerator:
    """
    Servicio de Inteligencia Artificial para la generación automática de descripciones
    de productos de alimentación premium de Fenix.
    Realiza OCR visual del envase a partir de la imagen principal utilizando Gemini 2.5 Flash.
    """

    @staticmethod
    def fetch_product_image_bytes(product):
        """
        Intenta recuperar los bytes de la imagen del producto de forma robusta.
        Soporta almacenamiento local de desarrollo y GCS en producción.
        """
        if not product.image:
            return None, None

        image_bytes = None
        mime_type = None

        # Intento 1: Leer directamente de la ruta o storage local
        try:
            product.image.open('rb')
            image_bytes = product.image.read()
            product.image.close()
            
            mime_type, _ = mimetypes.guess_type(product.image.name)
            if not mime_type:
                mime_type = 'image/jpeg'
                
            logger.info(f"[DescriptionGenerator] Imagen cargada directamente de storage para {product.name_es}")
            return image_bytes, mime_type
        except Exception as e:
            logger.warning(f"[DescriptionGenerator] No se pudo leer la imagen directamente del campo de base de datos ({e}). Intentando fallback HTTP...")

        # Intento 2: Fallback vía HTTP GET usando la URL robusta del modelo
        image_url = product.image_url
        if not image_url:
            return None, None

        try:
            # Si es una ruta local relativa en dev, intentar cargarla del sistema de archivos usando MEDIA_ROOT
            if image_url.startswith('/'):
                local_path = os.path.join(settings.MEDIA_ROOT, product.image.name)
                if os.path.exists(local_path):
                    with open(local_path, 'rb') as f:
                        image_bytes = f.read()
                    mime_type, _ = mimetypes.guess_type(local_path)
                    if not mime_type:
                        mime_type = 'image/jpeg'
                    logger.info(f"[DescriptionGenerator] Imagen cargada de ruta local relativa: {local_path}")
                    return image_bytes, mime_type

            # En desarrollo local o producción remota con URLs absolutas
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                image_bytes = response.content
                mime_type = response.headers.get('Content-Type', 'image/jpeg')
                logger.info(f"[DescriptionGenerator] Imagen cargada con éxito por HTTP GET de: {image_url}")
                return image_bytes, mime_type
            else:
                logger.error(f"[DescriptionGenerator] Error HTTP {response.status_code} al descargar la imagen de: {image_url}")
        except Exception as ex:
            logger.error(f"[DescriptionGenerator] Falló la descarga de la imagen por URL fallback para {product.name_es}: {ex}")

        return None, None

    @classmethod
    def generate_description_from_image(cls, product):
        """
        Genera la descripción comercial del producto analizando la imagen.
        Si no hay imagen o falla, genera una excelente descripción de fallback utilizando metadatos de BBDD.
        """
        api_key = getattr(settings, 'GOOGLE_API_KEY', '')
        if not api_key:
            logger.error("[DescriptionGenerator] GOOGLE_API_KEY no configurada en settings.")
            return "Descripción no disponible actualmente."

        # Configurar la API de Gemini
        genai.configure(api_key=api_key)
        
        # Usamos gemini-2.5-flash por su velocidad y excelente visión/OCR
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Intentar obtener la imagen del producto
        image_bytes, mime_type = cls.fetch_product_image_bytes(product)

        # Preparar datos textuales complementarios del producto
        promo_label = dict(product.PROMO_LABELS).get(product.promo_label, "") if product.promo_label else ""
        unit = product.unit_display or "unidad"
        price_info = f"{product.price}€ por {unit}" if product.price else ""
        
        context_data = (
            f"DATOS DE REFERENCIA DEL PRODUCTO (BBDD):\n"
            f"- Nombre comercial: {product.name_es}\n"
            f"- Formato o unidad de venta: {unit}\n"
            f"- Precio: {price_info}\n"
            f"- Etiqueta promocional: {promo_label}\n"
        )

        if image_bytes:
            # prompt con Imagen (OCR + Análisis visual)
            prompt = (
                f"{context_data}\n"
                f"INSTRUCCIONES DE GENERACIÓN:\n"
                f"Analiza la imagen del envase del producto y realiza OCR del texto visible para extraer información real:\n"
                f"1. Identifica la marca, el nombre exacto, la variedad/sabor, formato/peso, y claims comerciales.\n"
                f"2. Con esta información visual y los datos de referencia provistos, redacta una descripción comercial breve, atractiva y muy profesional para una ficha de catálogo B2B orientada a hostelería y tiendas de alimentación.\n"
                f"3. REGLA DE ORO DE SEGURIDAD: Tienes terminantemente prohibido inventar ingredientes específicos, alérgenos, certificaciones o propiedades que no se muestren visiblemente de forma clara en la imagen del envase. Si no los ves, no los listes.\n"
                f"4. Tono: Elegante, comercial, natural, amigable y orientado a la venta. No repitas el nombre de forma robótica.\n"
                f"5. Longitud: Entre 200 y 400 caracteres máximo. No utilices listas ni encabezados markdown. Redacta un párrafo continuo, fluido y pulido.\n"
            )
            
            image_data = {
                'mime_type': mime_type,
                'data': image_bytes
            }
            
            try:
                logger.info(f"[DescriptionGenerator] Enviando solicitud multimodal de visión para '{product.name_es}'...")
                response = model.generate_content([prompt, image_data])
                text = response.text.strip()
                # Limpiar posibles bloques de código markdown que Gemini pudiera meter
                if text.startswith("```"):
                    text = text.replace("```", "").strip()
                return text[:450] # Forzar límite físico de seguridad
            except Exception as e:
                logger.error(f"[DescriptionGenerator] Error en llamada multimodal a Gemini: {e}. Activando fallback textual...")

        # Fallback textual (Si no hay imagen o falla la llamada visual)
        fallback_prompt = (
            f"{context_data}\n"
            f"INSTRUCCIONES DE GENERACIÓN (FALLBACK SIN IMAGEN):\n"
            f"Redacta una descripción comercial elegante, profesional y breve para un producto alimentario premium de catálogo B2B, basándote únicamente en los datos de referencia provistos.\n"
            f"No inventes propiedades nutricionales ni alérgenos. Crea un párrafo breve, continuo, amigable y sumamente atractivo para hostelería.\n"
            f"Longitud: Entre 200 y 350 caracteres. No uses markdown de listas ni títulos.\n"
        )

        try:
            logger.info(f"[DescriptionGenerator] Generando descripción textual de fallback para '{product.name_es}'...")
            response = model.generate_content(fallback_prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.replace("```", "").strip()
            return text[:450]
        except Exception as e:
            logger.error(f"[DescriptionGenerator] Error crítico en fallback de Gemini: {e}")
            return f"Excelente producto de alimentación premium ideal para hostelería y restauración, presentado en formato conveniente de {unit} con la máxima calidad que caracteriza a Fenix."

    @classmethod
    def generate_and_translate_for_product(cls, product):
        """
        Genera la descripción del producto en español y la traduce automáticamente al chino simplificado.
        Retorna: dict con 'description_es' y 'description_zh_hans'
        """
        desc_es = cls.generate_description_from_image(product)
        desc_zh_hans = ""
        
        if desc_es and desc_es != "Descripción no disponible actualmente.":
            try:
                logger.info(f"[DescriptionGenerator] Traduciendo descripción generada de '{product.name_es}' al chino...")
                desc_zh_hans = translate_text(desc_es, source_lang='es', target_lang='zh-CN')
            except Exception as e:
                logger.warning(f"[DescriptionGenerator] Falló la traducción de la descripción: {e}")
                
        return {
            'description_es': desc_es,
            'description_zh_hans': desc_zh_hans or desc_es
        }
