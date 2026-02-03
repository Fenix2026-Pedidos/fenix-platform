from django.db import models
from django.utils.translation import gettext_lazy as _
from orders.models import Order
from accounts.models import User


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
