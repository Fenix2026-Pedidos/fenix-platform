import logging
import threading
from email.utils import formataddr
from typing import List, Dict

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from core.models import PlatformSettings
from orders.models import Order

logger = logging.getLogger(__name__)


def enqueue_order_confirmation_email(order_id: int) -> None:
    """Launch order confirmation email in a background thread."""

    thread = threading.Thread(
        target=_send_order_confirmation_email_safe,
        args=(order_id,),
        name=f'order-email-{order_id}',
        daemon=True,
    )
    thread.start()


def _send_order_confirmation_email_safe(order_id: int) -> None:
    try:
        _send_order_confirmation_email(order_id)
    except Exception:
        logger.exception('Error enviando email del pedido %s', order_id)


def _send_order_confirmation_email(order_id: int) -> None:
    try:
        order = (
            Order.objects.select_related('customer')
            .prefetch_related('items')
            .get(pk=order_id)
        )
    except Order.DoesNotExist:
        logger.warning('Pedido %s no encontrado; no se envía email', order_id)
        return

    platform_settings = PlatformSettings.get_settings()
    recipient = _resolve_recipient(platform_settings)
    if not recipient:
        logger.warning('Email de notificación no configurado; se omite pedido %s', order_id)
        return

    from_email = _resolve_from_email(platform_settings)
    context = _build_email_context(order)

    subject = f'Nuevo pedido recibido – Pedido #{order.id}'
    text_body = render_to_string('emails/order_created.txt', context)
    html_body = render_to_string('emails/order_created.html', context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[recipient],
    )
    # Futuras CC/BCC podrán configurarse estableciendo message.cc / message.bcc
    message.attach_alternative(html_body, 'text/html')
    message.send(fail_silently=False)
    logger.info('Email de pedido %s enviado a %s', order.id, recipient)


def _resolve_recipient(platform_settings: PlatformSettings) -> str:
    configured = (platform_settings.order_notification_email or '').strip()
    if configured:
        return configured
    return getattr(settings, 'DEFAULT_ORDER_NOTIFICATION_EMAIL', 'plataformafenix2026@gmail.com')


def _resolve_from_email(platform_settings: PlatformSettings) -> str:
    sender_email = platform_settings.email_from or settings.DEFAULT_FROM_EMAIL
    sender_name = platform_settings.email_from_name or 'FENIX'
    return formataddr((sender_name, sender_email))


def _build_email_context(order: Order) -> Dict[str, object]:
    local_datetime = timezone.localtime(order.created_at)
    items_payload: List[Dict[str, object]] = [
        {
            'name': item.product_name_es,
            'unit_price': item.unit_price,
            'quantity': item.quantity,
            'subtotal': item.line_total,
        }
        for item in order.items.all()
    ]

    return {
        'order': order,
        'order_datetime': local_datetime,
        'customer_name': order.customer.full_name or order.customer.email,
        'customer_email': order.customer.email,
        'items': items_payload,
        'total': order.total_amount,
        'currency': getattr(settings, 'DEFAULT_ORDER_CURRENCY', 'EUR'),
        'status_label': order.get_status_display(),
    }


__all__ = ['enqueue_order_confirmation_email']
