import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from catalog.models import Product
from ai_assistant.description_generator import DescriptionGenerator

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Genera descripciones comerciales automáticas usando Visión IA (OCR) para productos sin descripción."

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Fuerza la generación de descripciones para TODOS los productos activos, sobrescribiendo las existentes.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta el proceso llamando al API de Gemini para previsualizar los resultados sin guardar nada en base de datos.',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='ID específico de un producto a procesar.',
        )

    def handle(self, *args, **options):
        is_all = options['all']
        dry_run = options['dry_run']
        product_id = options.get('id')

        if dry_run:
            self.stdout.write(self.style.WARNING("Modo DRY-RUN activo. No se realizarán cambios persistentes en la base de datos."))

        # 1. Obtener productos activos o específicos
        if product_id:
            products = Product.objects.filter(pk=product_id)
            total_initial = products.count()
        else:
            products = Product.objects.filter(is_active=True)
            total_initial = products.count()

            # 2. Filtrar si no es --all
            if not is_all:
                products = [
                    p for p in products 
                    if not p.description_es or 
                    p.description_es.strip() == "" or 
                    "Sin descripción disponible" in p.description_es
                ]
            else:
                products = list(products)

        total_to_process = len(products)
        self.stdout.write(f"Encontrados {total_to_process} productos activos de {total_initial} totales para procesar.")

        if total_to_process == 0:
            self.stdout.write(self.style.SUCCESS("No hay productos que requieran descripción. Proceso terminado."))
            return

        success_count = 0
        error_count = 0

        for idx, product in enumerate(products, 1):
            self.stdout.write(f"\n[{idx}/{total_to_process}] Procesando: {product.name_es} (ID: {product.pk})")
            
            if product.image:
                self.stdout.write(f"  -> Imagen detectada: {product.image.name}")
            else:
                self.stdout.write("  -> Sin imagen. Usando generación basada en metadatos.")

            try:
                # Generar descripción
                result = DescriptionGenerator.generate_and_translate_for_product(product)
                desc_es = result.get('description_es', '')
                desc_zh = result.get('description_zh_hans', '')

                if not desc_es:
                    self.stdout.write(self.style.ERROR(f"  x Falló la generación para ID {product.pk}: Sin texto devuelto."))
                    error_count += 1
                    continue

                try:
                    self.stdout.write(self.style.SUCCESS(f"  + Descripción Generada (ES): {desc_es}"))
                    self.stdout.write(self.style.SUCCESS(f"  + Traducción Generada (ZH): {desc_zh}"))
                except Exception:
                    try:
                        self.stdout.write("  + Descripcion generada con exito (ES/ZH) - Omitida impresion por codificacion de consola.")
                    except Exception:
                        pass

                if not dry_run:
                    # Guardar campos
                    product.description_es = desc_es
                    product.description_zh_hans = desc_zh
                    product.description_ai_generated = True
                    product.description_source = 'image_ocr' if product.image else 'ai_enriched'
                    product.description_last_generated_at = timezone.now()
                    product.save()
                    self.stdout.write("  -> Guardado con éxito en la Base de Datos.")
                else:
                    self.stdout.write("  -> [DRY-RUN] Simulación de guardado realizada.")

                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  x Error crítico procesando ID {product.pk}: {e}"))
                error_count += 1

            # Pausa inteligente de cortesía para respetar la cuota de peticiones por minuto de Gemini API
            if idx < total_to_process:
                time.sleep(2)

        self.stdout.write("\n" + "="*50)
        status_msg = f"PROCESO TERMINADO. Éxito: {success_count} | Errores: {error_count}"
        if dry_run:
            self.stdout.write(self.style.WARNING(status_msg + " (Modo DRY-RUN)"))
        else:
            self.stdout.write(self.style.SUCCESS(status_msg))
        self.stdout.write("="*50)
