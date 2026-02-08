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
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))
    stock_available = models.IntegerField(default=0, verbose_name=_('Stock Disponible'))
    stock_min_threshold = models.IntegerField(default=0, verbose_name=_('Stock Mínimo'))
    stock_status = models.CharField(
        max_length=10,
        choices=STOCK_STATUS_CHOICES,
        default=STOCK_OK,
        verbose_name=_('Estado Stock')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha Creación'))

    class Meta:
        verbose_name = _('Producto')
        verbose_name_plural = _('Productos')
        ordering = ['name_es']

    def update_stock_status(self) -> None:
        if self.stock_available <= 0:
            self.stock_status = self.STOCK_OUT
        elif self.stock_available <= self.stock_min_threshold:
            self.stock_status = self.STOCK_LOW
        else:
            self.stock_status = self.STOCK_OK

    def save(self, *args, **kwargs):
        self.update_stock_status()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.name_es} / {self.name_zh_hans}'
