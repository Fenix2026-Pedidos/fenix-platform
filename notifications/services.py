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
    Crea una Notification para el usuario y envía email según su idioma.
    Si no se pasan subject/message, se usan los defaults de DEFAULT_MESSAGES.
    """
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
    subject, body = _pick_by_lang(sub_es, sub_zh, msg_es, msg_zh, lang)

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@fenix.com')
    try:
        ps = PlatformSettings.get_settings()
        from_email = f'{ps.email_from_name} <{ps.email_from}>'
    except Exception:
        pass

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=True,
        )
        logger.info('Email enviado a %s por evento %s (pedido %s)', user.email, event_type, order_id)
    except Exception as e:
        logger.warning('Error enviando email a %s: %s', user.email, e)

    return n
