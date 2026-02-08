from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import User


class Notification(models.Model):
    EVENT_ORDER_CREATED = 'order_created'
    EVENT_ORDER_CONFIRMED = 'order_confirmed'
    EVENT_ORDER_OUT_FOR_DELIVERY = 'order_out_for_delivery'
    EVENT_ORDER_DELIVERED = 'order_delivered'
    EVENT_ORDER_CANCELLED = 'order_cancelled'
    EVENT_ETA_UPDATED = 'eta_updated'
    EVENT_ORDER_LATE = 'order_late'

    EVENT_CHOICES = [
        (EVENT_ORDER_CREATED, _('Pedido creado')),
        (EVENT_ORDER_CONFIRMED, _('Pedido confirmado')),
        (EVENT_ORDER_OUT_FOR_DELIVERY, _('En reparto')),
        (EVENT_ORDER_DELIVERED, _('Entregado')),
        (EVENT_ORDER_CANCELLED, _('Cancelado')),
        (EVENT_ETA_UPDATED, _('ETA modificada')),
        (EVENT_ORDER_LATE, _('Pedido fuera de ETA')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Usuario')
    )
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES, verbose_name=_('Tipo de Evento'))
    subject_es = models.CharField(max_length=200, verbose_name=_('Asunto (ES)'))
    subject_zh_hans = models.CharField(max_length=200, verbose_name=_('Asunto (中文)'))
    message_es = models.TextField(verbose_name=_('Mensaje (ES)'))
    message_zh_hans = models.TextField(verbose_name=_('Mensaje (中文)'))
    is_read = models.BooleanField(default=False, verbose_name=_('Leído'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha'))

    class Meta:
        verbose_name = _('Notificación')
        verbose_name_plural = _('Notificaciones')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user_id} - {self.event_type}'
