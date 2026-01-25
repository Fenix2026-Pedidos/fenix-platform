from django.db import models


class Product(models.Model):
    STOCK_OK = 'ok'
    STOCK_LOW = 'low'
    STOCK_OUT = 'out'

    STOCK_STATUS_CHOICES = [
        (STOCK_OK, 'OK'),
        (STOCK_LOW, 'Bajo stock'),
        (STOCK_OUT, 'Sin stock'),
    ]

    name_es = models.CharField(max_length=200)
    name_zh_hans = models.CharField(max_length=200)
    description_es = models.TextField(blank=True)
    description_zh_hans = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text='Imagen del producto (recomendado: 800x600px)'
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    stock_available = models.IntegerField(default=0)
    stock_min_threshold = models.IntegerField(default=0)
    stock_status = models.CharField(
        max_length=10,
        choices=STOCK_STATUS_CHOICES,
        default=STOCK_OK,
    )
    created_at = models.DateTimeField(auto_now_add=True)

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
