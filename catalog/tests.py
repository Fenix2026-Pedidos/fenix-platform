from django.test import TestCase
from .models import Product, PromotionalProduct

class PromotionalProductTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name_es="Producto Test",
            price=10.50,
            unit_display="kg",
            is_active=True
        )

    def test_inheritance_fallback(self):
        """Verify that PromotionalProduct inherits fields from Product when blank."""
        promo = PromotionalProduct.objects.create(
            product=self.product,
            promo_title="",
            is_active=True
        )
        self.assertEqual(promo.display_title, "Producto Test")
        self.assertEqual(promo.display_price, 10.50)
        self.assertEqual(promo.display_unit, "kg")

    def test_manual_override(self):
        """Verify that PromotionalProduct uses manual fields when provided."""
        promo = PromotionalProduct.objects.create(
            product=self.product,
            promo_title="Título Especial",
            is_active=True
        )
        self.assertEqual(promo.display_title, "Título Especial")
        self.assertEqual(promo.display_price, 10.50) # Price is always from catalog
