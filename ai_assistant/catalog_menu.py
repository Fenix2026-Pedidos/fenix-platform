import unicodedata
import logging
from catalog.models import Product
from django.urls import reverse

logger = logging.getLogger(__name__)

def normalize_text(text):
    if not text:
        return ''
    nfkd = unicodedata.normalize('NFKD', str(text).lower().strip())
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

def get_catalog_facets():
    """
    Agrupa dinámicamente los productos activos del catálogo por tipo (categoría),
    características especiales y etiquetas promocionales, contando las unidades reales.
    Excluye cualquier sección que no tenga productos activos para garantizar la consistencia.
    """
    try:
        products = Product.objects.filter(is_active=True).values(
            'id', 'name_es', 'description_es', 'promo_label', 'is_new', 'is_best_seller', 'is_offer'
        )
        
        # 1. Mappings exactos de categorías/tipos definidos en catalog/views.py
        category_mappings = {
            'sandwich': ['sándwich', 'sandwich', 'sandw'],
            'salchichas': ['salchicha', 'frankfurt', 'salchichón', 'salchichon', 'big classic', 'big pavo', 'big pollo', 'big queso', 'viena', 'bratwurst', 'hot dog'],
            'pizzas': ['pizza', 'pizzas'],
            'jamon-cocido': ['jamón cocido', 'jamon cocido', 'york', 'cocido', 'fiambre'],
            'jamon-curado': ['jamón curado', 'jamon curado', 'jamón serrano', 'jamon serrano', 'curado 1954', 'bodega', 'reserva', 'gran reserva'],
            'pavo': ['pavo', 'pechuga pavo', 'fiambre pavo'],
            'pollo': ['pollo', 'pechuga pollo', 'fiambre pollo'],
            'charcuteria': ['mortadela', 'chopped', 'choppep', 'chorizo', 'salami', 'cervelat', 'cabeza jabalí', 'bacon', 'lacón', 'lacon', 'panceta', 'taquito', 'tiras', 'sarta', 'embutido', 'charcutería', 'charcuteria'],
            'curados': ['caña de lomo', 'caña lomo', 'caña', 'salchichón', 'salchichon', 'semicurado', 'fuet', 'fuetería', 'fueteria', 'chorizo curado', 'sarta'],
            'ibericos': ['ibérico', 'iberico', 'bellota', 'pata negra', 'cebo'],
            'fuet': ['fuet', 'fuetería', 'fueteria', 'espetec'],
        }
        
        category_labels = {
            'sandwich': "Sándwich",
            'salchichas': "Salchichas",
            'pizzas': "Pizzas",
            'jamon-cocido': "Jamón Cocido y York",
            'jamon-curado': "Jamón Curado",
            'pavo': "Pavo",
            'pollo': "Pollo",
            'charcuteria': "Charcutería",
            'curados': "Curados",
            'ibericos': "Ibéricos",
            'fuet': "Fuet",
        }
        
        # 2. Mappings de características especiales
        feature_mappings = {
            'sin-lactosa':      ['sin lactosa', 'no lactose', 'lactosa'],
            'sin-conservantes': ['sin conservantes', 'no preservatives', 'conservantes'],
            'sin-colorantes':   ['sin colorantes', 'no artificial colors', 'colorantes'],
            'sin-azucares':     ['sin azucares', 'sin azúcar', 'sin azucar', 'no sugar'],
        }
        
        feature_labels = {
            'sin-lactosa': "Sin lactosa",
            'sin-conservantes': "Sin conservantes",
            'sin-colorantes': "Sin colorantes",
            'sin-azucares': "Sin azúcares",
        }

        # Inicialización de contadores
        type_counts = {slug: 0 for slug in category_mappings}
        feature_counts = {slug: 0 for slug in feature_mappings}
        tag_counts = {
            'ofertas': 0,
            'novedades': 0,
            'mas-vendidos': 0
        }
        
        total_products = len(products)
        
        # Agregación ultra rápida en una sola pasada en Python
        for p in products:
            name_lower = p['name_es'].lower()
            desc_lower = p['description_es'].lower() if p['description_es'] else ''
            text_to_search = f"{name_lower} {desc_lower}"
            norm_to_search = normalize_text(text_to_search)
            
            # Categorías
            for slug, keywords in category_mappings.items():
                found = False
                for kw in keywords:
                    kw_lower = kw.lower()
                    kw_norm = normalize_text(kw_lower)
                    if kw_lower in text_to_search or kw_norm in norm_to_search:
                        found = True
                        break
                if found:
                    type_counts[slug] += 1
            
            # Características
            for slug, keywords in feature_mappings.items():
                found = False
                for kw in keywords:
                    kw_lower = kw.lower()
                    kw_norm = normalize_text(kw_lower)
                    if kw_lower in text_to_search or kw_norm in norm_to_search:
                        found = True
                        break
                if found:
                    feature_counts[slug] += 1
            
            # Etiquetas promocionales
            promo_lbl = p['promo_label']
            is_o = p['is_offer'] or (promo_lbl in ['oferta_semana', 'oferta_flash', 'super_oferta', 'mejor_precio'])
            is_n = p['is_new'] or (promo_lbl == 'novedad')
            is_b = p['is_best_seller'] or (promo_lbl == 'mas_vendido')
            
            if is_o:
                tag_counts['ofertas'] += 1
            if is_n:
                tag_counts['novedades'] += 1
            if is_b:
                tag_counts['mas-vendidos'] += 1

        # Generar lista de urls usando Django reverse de manera dinámica y limpia
        catalog_root = reverse('catalog:product_list')
        
        types_list = [
            {"label": category_labels[slug], "slug": slug, "count": count, "url": f"{catalog_root}?type={slug}"}
            for slug, count in type_counts.items() if count > 0
        ]
        # Ordenar tipos por cantidad de productos descendente (popularidad comercial)
        types_list.sort(key=lambda x: x['count'], reverse=True)
        
        features_list = [
            {"label": feature_labels[slug], "slug": slug, "count": count, "url": f"{catalog_root}?features={slug}"}
            for slug, count in feature_counts.items() if count > 0
        ]
        features_list.sort(key=lambda x: x['count'], reverse=True)
        
        tag_labels = {
            'ofertas': "Ofertas",
            'novedades': "Novedades",
            'mas-vendidos': "Más vendidos"
        }
        
        tags_list = [
            {"label": tag_labels[slug], "slug": slug, "count": count, "url": f"{catalog_root}?tag={slug}"}
            for slug, count in tag_counts.items() if count > 0
        ]
        
        return {
            "totalProducts": total_products,
            "types": types_list,
            "specialFeatures": features_list,
            "tags": tags_list,
            "root_url": catalog_root
        }
        
    except Exception as e:
        logger.error(f"[CatalogMenu] Error al generar facetas: {e}")
        # Fallback seguro en caso de error
        return {
            "totalProducts": 0,
            "types": [],
            "specialFeatures": [],
            "tags": [],
            "root_url": "/"
        }

def build_smart_menu_prompt():
    """
    Construye un bloque descriptivo estructurado de las categorías reales de stock
    para inyectarlo dinámicamente en el contexto del prompt del asistente.
    """
    facets = get_catalog_facets()
    total = facets["totalProducts"]
    root = facets["root_url"]
    
    prompt = f"""
--- MENÚ INTELIGENTE DEL CATÁLOGO REAL DE FENIX (DINÁMICO DESDE BASE DE DATOS) ---
Total productos activos en el catálogo: {total}
URL del catálogo completo: {root}

Categorías principales disponibles (tipos de producto):
"""
    # Listar categorías principales con urls
    for t in facets["types"]:
        prompt += f"- {t['label']} ({t['count']} productos) -> URL: {t['url']}\n"
        
    prompt += "\nCaracterísticas especiales y alérgenos disponibles:\n"
    for f in facets["specialFeatures"]:
        prompt += f"- {f['label']} ({f['count']} productos) -> URL: {f['url']}\n"
        
    prompt += "\nEtiquetas comerciales disponibles:\n"
    for tg in facets["tags"]:
        prompt += f"- {tg['label']} ({tg['count']} productos) -> URL: {tg['url']}\n"
        
    prompt += f"""
REGLA CRÍTICA DE INTERACCIÓN Y MENÚ:
Cuando el usuario te pregunte por "catálogo", "productos", "categorías", "tipos de producto", "ofertas", "recomendaciones" o similares, debes responder con un saludo comercial cordial y dibujar el Menú Inteligente del Catálogo EXACTAMENTE en formato de enlaces markdown: `[Texto de la Opción](URL)`.
Ejemplo:
🍽️ ¿Qué tipo de producto estás buscando?
[Todos los productos]({root})
[Sándwich]({root}?type=sandwich) [Salchichas]({root}?type=salchichas) ...

Respeta la siguiente guía UX de visualización para que la interfaz los renderice como botones interactivos en cuadrícula:
1. Pon el enlace de "Todos los productos" primero.
2. Agrupa el resto de categorías separadas por espacios simples en la misma línea para que se muestren de forma compacta (ej: `[Sándwich](URL) [Salchichas](URL) [Pizzas](URL) [Jamón Cocido y York](URL) ...`).
3. Muestra un máximo de 8 a 10 opciones de alta relevancia. Si hay más categorías, incluye al final un botón `[Ver más categorías]({root})`.
4. El menú de opciones debe basarse única y exclusivamente en los nombres de categorías provistos arriba. ¡NUNCA inventes categorías que no tengan productos activos!
--- FIN DE INFORMACIÓN DE CATÁLOGO DINÁMICO ---
"""
    return prompt
