from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from catalog.models import Product


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PREPARING = 'preparing'
    STATUS_OUT_FOR_DELIVERY = 'out_for_delivery'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, _('Nuevo')),
        (STATUS_CONFIRMED, _('Confirmado')),
        (STATUS_PREPARING, _('Preparando')),
        (STATUS_OUT_FOR_DELIVERY, _('En reparto')),
        (STATUS_DELIVERED, _('Entregado')),
        (STATUS_CANCELLED, _('Cancelado')),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='orders',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )
    eta_start = models.DateTimeField(null=True, blank=True)
    eta_end = models.DateTimeField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_deducted = models.BooleanField(
        default=False,
        help_text='True cuando el stock se ha descontado al pasar a Preparando',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'Order {self.id} - {self.customer.email}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
    )
    product_name_es = models.CharField(max_length=200)
    product_name_zh_hans = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.product_name_es} x {self.quantity}'


class OrderEvent(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='events',
    )
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='order_events',
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'{self.order_id} - {self.status}'
