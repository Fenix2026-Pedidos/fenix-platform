from django.db import models
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    STOCK_OK = 'ok'
    STOCK_LOW = 'low'
    STOCK_OUT = 'out'

    STOCK_STATUS_CHOICES = [
        (STOCK_OK, 'OK'),
        (STOCK_LOW, 'Bajo stock'),
        (STOCK_OUT, 'Sin stock'),
    ]

    name_es = models.CharField(max_length=200, verbose_name=_('Nombre (ES)'))
    name_zh_hans = models.CharField(max_length=200, verbose_name=_('Nombre (中文)'))
    description_es = models.TextField(blank=True, verbose_name=_('Descripción (ES)'))
    description_zh_hans = models.TextField(blank=True, verbose_name=_('Descripción (中文)'))
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text='Imagen del producto (recomendado: 800x600px)',
        verbose_name=_('Imagen')
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('Precio'))
    unit_display = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Ejemplo: "100 g", "1 Kg", "Unidad". Aparecerá junto al precio: 1,00€ / 100 g'),
        verbose_name=_('Unidad de medida')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))
    stock_available = models.IntegerField(default=0, verbose_name=_('Stock Disponible'))
    stock_min_threshold = models.IntegerField(default=0, verbose_name=_('Stock Mínimo'))
    stock_status = models.CharField(
        max_length=10,
        choices=STOCK_STATUS_CHOICES,
        default=STOCK_OK,
        verbose_name=_('Estado Stock')
    )
    is_new = models.BooleanField(default=False, verbose_name=_('Es Nuevo'))
    is_best_seller = models.BooleanField(default=False, verbose_name=_('Más Vendido'))
    is_offer = models.BooleanField(default=False, verbose_name=_('En Oferta'))
    catalog_order = models.PositiveIntegerField(default=0, verbose_name=_('Orden en catálogo'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha Creación'))

    class Meta:
        verbose_name = _('Producto')
        verbose_name_plural = _('Productos')
        ordering = ['catalog_order', 'name_es']

    def update_stock_status(self) -> None:
        if self.stock_available <= 0:
            self.stock_status = self.STOCK_OUT
        elif self.stock_available <= self.stock_min_threshold:
            self.stock_status = self.STOCK_LOW
        else:
            self.stock_status = self.STOCK_OK

    @property
    def translated_name(self):
        from django.utils.translation import get_language
        lang = get_language()
        if lang == 'zh-hans':
            return self.name_zh_hans or self.name_es
        return self.name_es

    @property
    def translated_description(self):
        from django.utils.translation import get_language
        lang = get_language()
        if lang == 'zh-hans':
            return self.description_zh_hans or self.description_es
        return self.description_es

    def save(self, *args, **kwargs):
        self.update_stock_status()
        return super().save(*args, **kwargs)

    @property
    def image_url(self) -> str:
        """
        Devuelve la URL de la imagen de forma robusta.
        1. Si no hay imagen, devuelve None.
        2. En producción (GCS), devuelve la URL de GCS.
        3. En local:
           - Si el archivo existe localmente, devuelve la URL local.
           - Si NO existe localmente, intenta devolver la URL de GCS como fallback 
             (útil para ver imágenes subidas en producción desde local).
        """
        if not self.image:
            return None
            
        from django.conf import settings
        import os
        
        try:
            # Caso 1: Producción o GCS configurado como storage por defecto
            if not settings.DEBUG or 'GoogleCloudStorage' in str(self.image.storage.__class__):
                return self.image.url
                
            # Caso 2: Desarrollo con FileSystemStorage
            # Verificar si el archivo existe físicamente en el disco local
            if os.path.exists(self.image.path):
                return self.image.url
            
            # Caso 3: Fallback a GCS si no existe en local pero tenemos el bucket configurado
            bucket_name = getattr(settings, 'GS_BUCKET_NAME', None)
            if bucket_name:
                return f"https://storage.googleapis.com/{bucket_name}/{self.image.name}"
                
            return self.image.url
        except Exception:
            # Fallback seguro al comportamiento por defecto de Django
            try:
                return self.image.url
            except:
                return None

    def __str__(self) -> str:
        return f'{self.name_es} / {self.name_zh_hans}'
