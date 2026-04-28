from django.core.management.base import BaseCommand
from catalog.models import Product
from ai_assistant.models import KnowledgeBase
from ai_assistant.services import AIService
from django.db import transaction

class Command(BaseCommand):
    help = 'Indexa los productos del catálogo en la base de conocimiento vectorial.'

    def handle(self, *args, **options):
        products = Product.objects.filter(is_active=True)
        self.stdout.write(f"Iniciando indexación de {products.count()} productos...")

        count = 0
        for product in products:
            # Construir un texto rico para el embedding
            content = f"""
            Producto: {product.name_es}
            Referencia: {product.reference or 'N/A'}
            Precio: {product.price}€ / {product.unit_display or 'unidad'}
            Descripción: {product.description_es}
            Disponibilidad: {'En stock' if product.stock_available > 0 else 'Agotado'}
            """.strip()

            metadata = {
                'source': 'Catalog',
                'product_id': product.id,
                'reference': product.reference,
                'type': 'product'
            }

            # Evitar duplicados si ya existe para este producto
            KnowledgeBase.objects.filter(metadata__product_id=product.id).delete()

            # Generar embedding
            embedding = AIService.get_embedding(content)
            
            if embedding:
                KnowledgeBase.objects.create(
                    content=content,
                    metadata=metadata,
                    embedding=embedding
                )
                count += 1
                if count % 10 == 0:
                    self.stdout.write(self.style.SUCCESS(f"Indexados {count} productos..."))
            else:
                self.stdout.write(self.style.WARNING(f"No se pudo generar embedding para: {product.name_es}"))

        self.stdout.write(self.style.SUCCESS(f"Proceso finalizado. {count} productos indexados con éxito."))
