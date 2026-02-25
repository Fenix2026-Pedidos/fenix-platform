"""
Servicio de notificaciones: crea Notification y envía email.
Prioridad de idioma: user.language -> platform.default_language -> es.
"""
import logging
from typing import Optional

from django.core.mail import send_mail
from django.conf import settings

from accounts.models import User
from core.models import PlatformSettings
from notifications.models import Notification
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
from .utils import generate_order_pdf

logger = logging.getLogger(__name__)

# Mensajes por defecto por tipo de evento (ES / zh-hans)
DEFAULT_MESSAGES = {
    Notification.EVENT_ORDER_CREATED: {
        'subject_es': 'Pedido #{id} creado',
        'subject_zh_hans': '订单 #{id} 已创建',
        'message_es': 'Su pedido #{id} ha sido registrado correctamente. Recibirá actualizaciones por email.',
        'message_zh_hans': '您的订单 #{id} 已成功登记。您将收到电子邮件更新。',
    },
    Notification.EVENT_ORDER_CONFIRMED: {
        'subject_es': 'Pedido #{id} confirmado',
        'subject_zh_hans': '订单 #{id} 已确认',
        'message_es': 'Su pedido #{id} ha sido confirmado y está en proceso.',
        'message_zh_hans': '您的订单 #{id} 已确认，正在处理中。',
    },
    Notification.EVENT_ORDER_OUT_FOR_DELIVERY: {
        'subject_es': 'Pedido #{id} en reparto',
        'subject_zh_hans': '订单 #{id} 配送中',
        'message_es': 'Su pedido #{id} está en camino.',
        'message_zh_hans': '您的订单 #{id} 正在配送中。',
    },
    Notification.EVENT_ORDER_DELIVERED: {
        'subject_es': 'Pedido #{id} entregado',
        'subject_zh_hans': '订单 #{id} 已送达',
        'message_es': 'Su pedido #{id} ha sido entregado. Gracias por su confianza.',
        'message_zh_hans': '您的订单 #{id} 已送达。感谢您的信任。',
    },
    Notification.EVENT_ORDER_CANCELLED: {
        'subject_es': 'Pedido #{id} cancelado',
        'subject_zh_hans': '订单 #{id} 已取消',
        'message_es': 'Su pedido #{id} ha sido cancelado. Si tiene dudas, contacte con nosotros.',
        'message_zh_hans': '您的订单 #{id} 已取消。如有疑问，请联系我们。',
    },
    Notification.EVENT_ETA_UPDATED: {
        'subject_es': 'Pedido #{id}: ETA actualizada',
        'subject_zh_hans': '订单 #{id}：预计送达时间已更新',
        'message_es': 'Se ha actualizado la ventana de entrega del pedido #{id}.',
        'message_zh_hans': '订单 #{id} 的预计送达时间已更新。',
    },
    Notification.EVENT_ORDER_LATE: {
        'subject_es': 'Pedido #{id}: retraso',
        'subject_zh_hans': '订单 #{id}：延迟',
        'message_es': 'Su pedido #{id} podría sufrir un retraso. Disculpe las molestias.',
        'message_zh_hans': '您的订单 #{id} 可能延迟。给您带来不便，敬请谅解。',
    },
}


def _lang(user: Optional[User]) -> str:
    """Prioridad: user.language -> platform default -> es."""
    if user and hasattr(user, 'language') and user.language:
        return user.language
    try:
        ps = PlatformSettings.get_settings()
        return ps.default_language or 'es'
    except Exception:
        return 'es'


def _pick_by_lang(sub_es: str, sub_zh: str, msg_es: str, msg_zh: str, lang: str) -> tuple[str, str]:
    if lang == 'zh-hans':
        return sub_zh, msg_zh
    return sub_es, msg_es


def send_order_notification(
    *,
    user: User,
    event_type: str,
    order_id: int,
    subject_es: Optional[str] = None,
    subject_zh_hans: Optional[str] = None,
    message_es: Optional[str] = None,
    message_zh_hans: Optional[str] = None,
    send_email: bool = True,
) -> Notification:
    """
    Crea una Notification para el usuario y envía email profesional según su idioma.
    Añade adjunto PDF si es un pedido nuevo.
    """
    from orders.models import Order
    try:
        order = Order.objects.prefetch_related('items__product').get(pk=order_id)
    except Order.DoesNotExist:
        logger.error('No se pudo enviar notificación: Pedido %s no existe', order_id)
        return None

    tpl = DEFAULT_MESSAGES.get(event_type)
    if tpl:
        sub_es = subject_es or tpl['subject_es'].format(id=order_id)
        sub_zh = subject_zh_hans or tpl['subject_zh_hans'].format(id=order_id)
        msg_es = message_es or tpl['message_es'].format(id=order_id)
        msg_zh = message_zh_hans or tpl['message_zh_hans'].format(id=order_id)
    else:
        sub_es = subject_es or 'Notificación'
        sub_zh = subject_zh_hans or '通知'
        msg_es = message_es or ''
        msg_zh = message_zh_hans or ''

    n = Notification.objects.create(
        user=user,
        event_type=event_type,
        subject_es=sub_es,
        subject_zh_hans=sub_zh,
        message_es=msg_es,
        message_zh_hans=msg_zh,
    )

    if not send_email:
        return n

    lang = _lang(user)
    
    # 1. Preparar Contexto Común
    ps = PlatformSettings.get_settings()
    items = order.items.all()
    subtotal = sum(item.line_total for item in items)
    
    context = {
        'order': order,
        'customer': order.customer,
        'items': items,
        'subtotal': subtotal,
        'shipping_cost': 0, # Se puede extender si hay gastos de envío
        'year': timezone.now().year,
        'now': timezone.now(),
        'platform_name': ps.email_from_name,
    }

    # 2. Asunto Especial para Pedidos Nuevos
    if event_type == Notification.EVENT_ORDER_CREATED:
        # [FENIX - {EMPRESA}] Nuevo pedido #{NUMERO_PEDIDO} – {NOMBRE_CLIENTE}
        company_name = ps.email_from_name or "FENIX"
        client_name = order.customer.full_name or order.customer.email
        subject = f"[{company_name}] Nuevo pedido #{order.id} – {client_name}"
    else:
        subject, _ = _pick_by_lang(sub_es, sub_zh, msg_es, msg_zh, lang)

    # 3. Generar PDF si es Pedido Nuevo
    pdf_file = None
    pdf_name = ""
    pdf_generation_failed = False
    
    if event_type == Notification.EVENT_ORDER_CREATED:
        pdf_file = generate_order_pdf(context)
        if not pdf_file:
            pdf_generation_failed = True
            logger.error("Error generando adjunto PDF para pedido %s", order.id)
        else:
            # Pedido_{NUMERO_PEDIDO}_{FECHA}.pdf
            date_str = order.created_at.strftime("%Y-%m-%d")
            pdf_name = f"Pedido_{order.id}_{date_str}.pdf"

    # 4. Renderizar Cuerpo HTML o Texto
    if event_type == Notification.EVENT_ORDER_CREATED:
        html_message = render_to_string('notifications/order_email.html', context)
        if pdf_generation_failed:
            html_message += f"<p style='color: red;'><strong>Nota:</strong> Adjunto pendiente de generación automática</p>"
        body = html_message
        is_html = True
    else:
        _, body = _pick_by_lang(sub_es, sub_zh, msg_es, msg_zh, lang)
        is_html = False

    from_email = f'{ps.email_from_name} <{ps.email_from}>'
    
    # 5. Configurar Destinatarios
    recipients = [user.email]
    if ps.order_notification_email and ps.order_notification_email not in recipients:
        recipients.append(ps.order_notification_email)

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=recipients,
        )
        if is_html:
            email.content_subtype = "html"
            
        if pdf_file:
            email.attach(pdf_name, pdf_file.getvalue(), "application/pdf")
            
        email.send(fail_silently=False)
        logger.info('Email de pedido %s enviado a %s', order_id, recipients)
    except Exception as e:
        logger.warning('Error enviando email de pedido %s: %s', order_id, e)

    return n
