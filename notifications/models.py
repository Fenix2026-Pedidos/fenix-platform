from django.db import models

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
        (EVENT_ORDER_CREATED, 'Pedido creado'),
        (EVENT_ORDER_CONFIRMED, 'Pedido confirmado'),
        (EVENT_ORDER_OUT_FOR_DELIVERY, 'En reparto'),
        (EVENT_ORDER_DELIVERED, 'Entregado'),
        (EVENT_ORDER_CANCELLED, 'Cancelado'),
        (EVENT_ETA_UPDATED, 'ETA modificada'),
        (EVENT_ORDER_LATE, 'Pedido fuera de ETA'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES)
    subject_es = models.CharField(max_length=200)
    subject_zh_hans = models.CharField(max_length=200)
    message_es = models.TextField()
    message_zh_hans = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user_id} - {self.event_type}'
