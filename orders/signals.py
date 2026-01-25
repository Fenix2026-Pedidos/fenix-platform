"""
Señales para el ciclo de vida del pedido.
- Descuento de stock cuando el pedido pasa a PREPARANDO.
- Notificaciones por email al crear o cambiar estado.
"""
import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Order
from notifications.models import Notification
from notifications.services import send_order_notification

logger = logging.getLogger(__name__)

# Cache de estado anterior (pre_save -> post_save) para detectar cambios
_prev_order_status: dict[int, str] = {}


@receiver(pre_save, sender=Order)
def _cache_old_order_status(sender, instance: Order, **kwargs):
    if instance.pk:
        try:
            old = Order.objects.only('status').get(pk=instance.pk)
            _prev_order_status[instance.pk] = old.status
        except Order.DoesNotExist:
            pass


def _emit_order_notifications(instance: Order, created: bool):
    if created:
        send_order_notification(
            user=instance.customer,
            event_type=Notification.EVENT_ORDER_CREATED,
            order_id=instance.pk,
        )
        return

    old = _prev_order_status.pop(instance.pk, None)
    if old == instance.status:
        return

    event = None
    if instance.status == Order.STATUS_CONFIRMED:
        event = Notification.EVENT_ORDER_CONFIRMED
    elif instance.status == Order.STATUS_OUT_FOR_DELIVERY:
        event = Notification.EVENT_ORDER_OUT_FOR_DELIVERY
    elif instance.status == Order.STATUS_DELIVERED:
        event = Notification.EVENT_ORDER_DELIVERED
    elif instance.status == Order.STATUS_CANCELLED:
        event = Notification.EVENT_ORDER_CANCELLED

    if event:
        send_order_notification(
            user=instance.customer,
            event_type=event,
            order_id=instance.pk,
        )


@receiver(post_save, sender=Order)
def on_order_saved(sender, instance: Order, created, **kwargs):
    # 1. Descuento de stock al pasar a PREPARANDO
    if instance.status == Order.STATUS_PREPARING and not instance.stock_deducted:
        updated_products = []
        for item in instance.items.select_related('product').all():
            product = item.product
            product.stock_available = max(0, product.stock_available - item.quantity)
            product.save()
            updated_products.append((product.id, item.quantity))
        if updated_products:
            Order.objects.filter(pk=instance.pk).update(stock_deducted=True)
            logger.info('Stock descontado por pedido %s: %s', instance.pk, updated_products)

    # 2. Notificaciones por email
    _emit_order_notifications(instance, created)
