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
        verbose_name=_('Cliente')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name=_('Estado')
    )
    eta_start = models.DateTimeField(null=True, blank=True, verbose_name=_('ETA Inicio'))
    eta_end = models.DateTimeField(null=True, blank=True, verbose_name=_('ETA Fin'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_('Total'))
    stock_deducted = models.BooleanField(
        default=False,
        help_text='True cuando el stock se ha descontado al pasar a Preparando',
        verbose_name=_('Stock Descontado')
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de Entrega'),
        help_text='Fecha y hora en que el pedido fue entregado (auto-set cuando status=DELIVERED)'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha Creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Última Actualización'))

    class Meta:
        verbose_name = _('Pedido')
        verbose_name_plural = _('Pedidos')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Pedido {self.id} - {self.customer.email}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Pedido')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('Producto')
    )
    product_name_es = models.CharField(max_length=200, verbose_name=_('Nombre (ES)'))
    product_name_zh_hans = models.CharField(max_length=200, verbose_name=_('Nombre (中文)'))
    quantity = models.PositiveIntegerField(verbose_name=_('Cantidad'))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('Precio Unitario'))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('Total Línea'))

    class Meta:
        verbose_name = _('Línea de Pedido')
        verbose_name_plural = _('Líneas de Pedido')

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
        verbose_name=_('Pedido')
    )
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES, verbose_name=_('Estado'))
    note = models.TextField(blank=True, verbose_name=_('Nota'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha'))
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='order_events',
        verbose_name=_('Creado por')
    )

    class Meta:
        verbose_name = _('Evento de Pedido')
        verbose_name_plural = _('Eventos de Pedidos')
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'{self.order_id} - {self.status}'


class OrderDocument(models.Model):
    """Documentos asociados a pedidos (facturas, comprobantes, etc.)"""
    
    DOC_TYPE_INVOICE = 'invoice'
    DOC_TYPE_RECEIPT = 'receipt'
    DOC_TYPE_SHIPMENT = 'shipment'
    DOC_TYPE_OTHER = 'other'
    
    DOC_TYPE_CHOICES = [
        (DOC_TYPE_INVOICE, _('Factura')),
        (DOC_TYPE_RECEIPT, _('Comprobante')),
        (DOC_TYPE_SHIPMENT, _('Guía de Envío')),
        (DOC_TYPE_OTHER, _('Otro')),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Pedido')
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOC_TYPE_CHOICES,
        default=DOC_TYPE_OTHER,
        verbose_name=_('Tipo de documento')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Título')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción')
    )
    file = models.FileField(
        upload_to='order_documents/%Y/%m/',
        verbose_name=_('Archivo')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='uploaded_documents',
        verbose_name=_('Subido por')
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de subida')
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = _('Documento de Pedido')
        verbose_name_plural = _('Documentos de Pedidos')
    
    def __str__(self):
        return f'{self.title} - Order #{self.order.id}'

