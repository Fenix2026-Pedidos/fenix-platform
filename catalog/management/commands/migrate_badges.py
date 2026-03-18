from django.core.management.base import BaseCommand
from catalog.models import Product, PromotionalProduct

class Command(BaseCommand):
    help = 'Migrates legacy is_new, is_best_seller, is_offer flags and PromotionalProduct labels to Product.promo_label'

    def handle(self, *args, **options):
        # 1. Migrate from PromotionalProduct (Highest priority)
        promos = PromotionalProduct.objects.filter(is_active=True, promo_label__isnull=False).exclude(promo_label='')
        count_promo = 0
        for promo in promos:
            product = promo.product
            if not product.promo_label:
                product.promo_label = promo.promo_label
                product.save()
                count_promo += 1
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {count_promo} labels from PromotionalProduct'))

        # 2. Migrate from legacy boolean flags
        # is_new -> novedad
        new_prods = Product.objects.filter(is_new=True, promo_label__isnull=True)
        count_new = new_prods.update(promo_label='novedad')
        self.stdout.write(self.style.SUCCESS(f'Migrated {count_new} "is_new" flags to "novedad"'))

        # is_best_seller -> mas_vendido
        best_prods = Product.objects.filter(is_best_seller=True, promo_label__isnull=True)
        count_best = best_prods.update(promo_label='mas_vendido')
        self.stdout.write(self.style.SUCCESS(f'Migrated {count_best} "is_best_seller" flags to "mas_vendido"'))

        # is_offer -> oferta_semana
        offer_prods = Product.objects.filter(is_offer=True, promo_label__isnull=True)
        count_offer = offer_prods.update(promo_label='oferta_semana')
        self.stdout.write(self.style.SUCCESS(f'Migrated {count_offer} "is_offer" flags to "oferta_semana"'))

        self.stdout.write(self.style.SUCCESS('Migration completed successfully'))
