import logging
import unicodedata
from django.core.management.base import BaseCommand
from django.conf import settings
from catalog.models import Product
from ai_assistant.models import KnowledgeBase
from ai_assistant.framework.rag import SynergIARAG

logger = logging.getLogger(__name__)

def normalize_text(text):
    if not text:
        return ''
    nfkd = unicodedata.normalize('NFKD', str(text).lower().strip())
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

class Command(BaseCommand):
    help = 'Sincroniza el catálogo de productos y el contexto de Fenix con la base de conocimientos vectorial (RAG) de Neus.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Inicializando la sincronización de catálogo con Neus..."))
        
        # 1. Limpiar base de conocimiento existente (fuente: catalog y system)
        KnowledgeBase.objects.filter(metadata__source__in=['catalog', 'system']).delete()
        self.stdout.write(self.style.SUCCESS("Conocimientos previos (catalog/system) borrados."))

        # Inicializar el gestor de RAG
        rag = SynergIARAG(getattr(settings, 'GOOGLE_API_KEY', ''))

        # 2. Inyectar Contexto General del Sistema (Fenix)
        system_contexts = [
            """
            Fenix es una plataforma B2B de distribución mayorista.
            La empresa Fenix se dedica a la venta y distribución de productos de alimentación premium para hostelería y comercios.
            Pedidos y Pagos: Fenix acepta pedidos directamente a través de la web, pero el pago se procesa posteriormente contra factura (condiciones a 30 o 60 días según cliente) mediante domiciliación bancaria.
            """,
            """
            Envíos y Logística de Fenix:
            Los envíos se realizan de forma urgente con logística especializada en frío para garantizar la cadena térmica de los alimentos.
            Los pedidos realizados antes de las 13:00 se entregan en 24/48 horas laborables en la península.
            El pedido mínimo es de 50€. El coste de envío es gratuito para pedidos superiores a 150€. Para pedidos inferiores, el coste es de 15€.
            """,
            """
            Para realizar pedidos por WhatsApp o contactar con soporte técnico de Fenix, el cliente puede usar el botón de WhatsApp presente en la plataforma.
            Neus es la asistente comercial digital inteligente de Fenix, especializada en ayudar a los clientes a encontrar productos en el catálogo, conocer precios, stock disponible, características como alérgenos (sin gluten, sin lactosa, etc) y recomendar promociones.
            Neus no puede procesar el cobro final, pero sí ayudar a llenar el carrito y gestionar la solicitud de pedido.
            """
        ]

        self.stdout.write("Procesando contexto de sistema...")
        for text in system_contexts:
            text = text.strip()
            embedding = rag.get_embedding(text)
            if embedding:
                KnowledgeBase.objects.create(
                    content=text,
                    metadata={'source': 'system', 'type': 'general_rules'},
                    embedding=embedding
                )

        # 3. Mapeo de Categorías y Características
        category_mappings = {
            'Sandwiches': ['sándwich', 'sandwich', 'sandw'],
            'Salchichas y Hot Dogs': ['salchicha', 'frankfurt', 'salchichón', 'salchichon', 'big classic', 'big pavo', 'big pollo', 'big queso', 'viena', 'bratwurst', 'hot dog'],
            'Pizzas': ['pizza', 'pizzas'],
            'Jamón Cocido': ['jamón cocido', 'jamon cocido', 'york', 'cocido', 'fiambre'],
            'Jamón Curado y Serrano': ['jamón curado', 'jamon curado', 'jamón serrano', 'jamon serrano', 'curado 1954', 'bodega', 'reserva', 'gran reserva'],
            'Pavo': ['pavo', 'pechuga pavo', 'fiambre pavo'],
            'Pollo': ['pollo', 'pechuga pollo', 'fiambre pollo'],
            'Charcutería Variada': ['mortadela', 'chopped', 'choppep', 'chorizo', 'salami', 'cervelat', 'cabeza jabalí', 'bacon', 'lacón', 'lacon', 'panceta', 'taquito', 'tiras', 'sarta', 'embutido', 'charcutería', 'charcuteria'],
            'Curados y Embutidos': ['caña de lomo', 'caña lomo', 'caña', 'salchichón', 'salchichon', 'semicurado', 'fuet', 'fuetería', 'fueteria', 'chorizo curado', 'sarta'],
            'Ibéricos': ['ibérico', 'iberico', 'bellota', 'pata negra', 'cebo'],
            'Fuet y Espetec': ['fuet', 'fuetería', 'fueteria', 'espetec'],
        }

        feature_mappings = {
            'Sin Lactosa': ['sin lactosa', 'no lactose', 'lactosa'],
            'Sin Conservantes': ['sin conservantes', 'no preservatives', 'conservantes'],
            'Sin Colorantes': ['sin colorantes', 'no artificial colors', 'colorantes'],
            'Sin Azúcares': ['sin azucares', 'sin azúcar', 'sin azucar', 'no sugar'],
        }

        # 4. Procesar Catálogo de Productos
        products = Product.objects.filter(is_active=True)
        count = 0
        self.stdout.write(f"Iniciando procesamiento de {products.count()} productos...")

        for product in products:
            # Buscar en el nombre y descripcion
            searchable_text = f"{product.name_es} {product.description_es}".lower()
            normalized_text = normalize_text(searchable_text)

            # Extraer categorías
            product_categories = []
            for cat_name, keywords in category_mappings.items():
                for kw in keywords:
                    if kw.lower() in searchable_text or normalize_text(kw) in normalized_text:
                        product_categories.append(cat_name)
                        break # Ya encontramos que pertenece a esta categoria

            # Extraer features
            product_features = []
            for feat_name, keywords in feature_mappings.items():
                for kw in keywords:
                    if kw.lower() in searchable_text or normalize_text(kw) in normalized_text:
                        product_features.append(feat_name)
                        break

            cat_str = ", ".join(product_categories) if product_categories else "General"
            feat_str = ", ".join(product_features) if product_features else "Ninguna especificada"
            stock_str = dict(Product.STOCK_STATUS_CHOICES).get(product.stock_status, 'Desconocido')
            promo_str = product.promo_label_display if product.promo_label_display else "Ninguna"

            content = (
                f"Catálogo de Productos Fenix - Información Comercial:\n"
                f"Nombre del Producto: {product.name_es}\n"
                f"Referencia (SKU): {product.reference or 'N/A'}\n"
                f"Precio: {product.price}€ por {product.unit_display or 'unidad'}\n"
                f"Estado de Stock: {stock_str} ({product.stock_available} unidades disponibles)\n"
                f"Promoción Activa: {promo_str}\n"
                f"Categorías a las que pertenece: {cat_str}\n"
                f"Características especiales y alérgenos: {feat_str}\n"
                f"Descripción del producto: {product.description_es or 'Sin descripción adicional.'}"
            )

            embedding = rag.get_embedding(content)
            if embedding:
                KnowledgeBase.objects.create(
                    content=content,
                    metadata={
                        'source': 'catalog',
                        'product_id': product.id,
                        'reference': product.reference,
                        'categories': product_categories,
                        'features': product_features
                    },
                    embedding=embedding
                )
                count += 1
                if count % 10 == 0:
                    self.stdout.write(f"Procesados {count}/{products.count()} productos...")

        self.stdout.write(self.style.SUCCESS(f"¡Sincronización completada con éxito! {count} productos indexados en la memoria de Neus."))
