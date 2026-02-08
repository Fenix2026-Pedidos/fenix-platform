"""
Utilidades para cuentas de usuario: tokens de verificación, helpers de roles, etc.
"""
import secrets
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _, gettext
from core.models import PlatformSettings


def get_user_language(user):
    """
    Obtiene el idioma del usuario según prioridad:
    1. user.language (si está autenticado)
    2. platform.default_language (PlatformSettings)
    3. 'es' (fallback)
    """
    if user.is_authenticated and hasattr(user, 'language') and user.language:
        return user.language
    
    try:
        platform = PlatformSettings.get_settings()
        if platform.default_language:
            return platform.default_language
    except Exception:
        pass
    
    return 'es'


def get_time_based_greeting():
    """
    Retorna saludo según la hora del día:
    - 05:00-11:59 → "Buenos días"
    - 12:00-19:59 → "Buenas tardes"
    - 20:00-04:59 → "Buenas noches"
    
    Usa gettext para i18n (no lazy, se evalúa al momento).
    """
    now = timezone.localtime(timezone.now())
    hour = now.hour
    
    if 5 <= hour < 12:
        return gettext("Buenos días")
    elif 12 <= hour < 20:
        return gettext("Buenas tardes")
    else:
        return gettext("Buenas noches")


def get_user_greeting(user):
    """
    Genera saludo personalizado completo para el usuario.
    Ejemplo: "¡Buenas tardes, Vladimir!"
    """
    greeting = get_time_based_greeting()
    name = user.first_name or user.display_name or user.email.split('@')[0]
    return f"¡{greeting}, {name}!"


def get_dashboard_status(user):
    """
    Retorna información de estado GLOBAL del dashboard (no operativo).
    
    El HERO responde a: "¿Tengo algo urgente ahora mismo?"
    Las tarjetas responden a: "Si entro aquí, ¿qué veré?"
    
    Returns:
        dict: {
            'message': str,
            'level': str ('success', 'warning', 'info', 'danger'),
            'icon': str (emoji o clase FA)
        }
    """
    from orders.models import Order
    from notifications.models import Notification
    
    try:
        has_urgent_items = False
        
        # Verificar si hay algo urgente (sin dar detalles operativos)
        if user.has_perm('orders.view_order'):
            pending_orders = Order.objects.filter(status='pending').count()
            if pending_orders > 0:
                has_urgent_items = True
        
        if hasattr(user, 'notifications'):
            unread = Notification.objects.filter(user=user, read=False).count()
            if unread > 0:
                has_urgent_items = True
        
        # Estado global - sin duplicar detalles de las tarjetas
        if has_urgent_items:
            return {
                'message': gettext("Hay elementos que requieren tu atención"),
                'level': 'warning',
                'icon': '⚠️'
            }
        
        # Estado tranquilo - mensaje global genérico
        return {
            'message': gettext("Todo está en orden por ahora"),
            'level': 'success',
            'icon': '✓'
        }
    except Exception:
        # Fallback seguro - mensaje genérico, no operativo
        return {
            'message': gettext("Plataforma operativa"),
            'level': 'success',
            'icon': '✓'
        }


def generate_email_verification_token():
    """Genera un token seguro para verificación de email"""
    return secrets.token_urlsafe(32)


def send_verification_email(user, verification_url):
    """
    Envía email de verificación al usuario con enlace de confirmación.
    Usa i18n según user.language -> platform.default_language -> es
    """
    from .models import EmailVerificationToken
    
    platform = PlatformSettings.get_settings()
    lang = user.language or platform.default_language or 'es'
    
    # Crear token de verificación
    token = EmailVerificationToken.objects.create(user=user)
    verification_link = f"{verification_url}?token={token.token}"
    
    if lang == 'zh-hans':
        subject = 'FENIX - 请验证您的电子邮件'
        message = f'您好 {user.full_name},\n\n'
        message += '感谢您注册 FENIX。\n\n'
        message += '请点击以下链接验证您的电子邮件地址：\n\n'
        message += f'{verification_link}\n\n'
        message += '此链接将在24小时后过期。\n\n'
        message += '此致，\nFENIX 团队'
    else:
        subject = 'FENIX - Verifica tu email'
        message = f'Hola {user.full_name},\n\n'
        message += 'Gracias por registrarte en FENIX.\n\n'
        message += 'Por favor, haz clic en el siguiente enlace para verificar tu dirección de email:\n\n'
        message += f'{verification_link}\n\n'
        message += 'Este enlace expirará en 24 horas.\n\n'
        message += 'Saludos,\nEquipo FENIX'
    
    from_email = platform.email_from or settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [user.email], fail_silently=False)


def send_approval_notification(user, approved=True):
    """
    Envía notificación al usuario cuando su cuenta es aprobada/rechazada.
    Usa i18n según user.language -> platform.default_language -> es
    """
    platform = PlatformSettings.get_settings()
    lang = user.language or platform.default_language or 'es'
    
    if approved:
        if lang == 'zh-hans':
            subject = 'FENIX - 您的账户已获批准'
            message = f'您好 {user.full_name},\n\n'
            message += '您的账户已被批准。现在可以登录 FENIX 了。\n\n'
            message += '此致，\nFENIX 团队'
        else:
            subject = 'FENIX - Tu cuenta ha sido aprobada'
            message = f'Hola {user.full_name},\n\n'
            message += 'Tu cuenta ha sido aprobada. Ya puedes iniciar sesión en FENIX.\n\n'
            message += 'Saludos,\nEquipo FENIX'
    else:
        if lang == 'zh-hans':
            subject = 'FENIX - 账户状态更新'
            message = f'您好 {user.full_name},\n\n'
            message += 'Lamentablemente, su solicitud de cuenta no ha sido aprobada.\n\n'
            message += '此致，\nFENIX 团队'
        else:
            subject = 'FENIX - Actualización de estado de cuenta'
            message = f'Hola {user.full_name},\n\n'
            message += 'Lamentablemente, tu solicitud de cuenta no ha sido aprobada.\n\n'
            message += 'Saludos,\nEquipo FENIX'
    
    from_email = platform.email_from or settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [user.email], fail_silently=False)


def is_manager_or_admin(user):
    """Helper para verificar si el usuario es Admin o Super Admin"""
    from accounts.models import User
    return (
        user.role in (User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN) or
        user.is_superuser or
        user.is_staff
    )


def send_new_user_admin_notification(user, request=None):
    """
    Envía notificación al administrador cuando un nuevo usuario se registra.
    """
    try:
        platform = PlatformSettings.get_settings()
        admin_email = getattr(settings, 'ADMIN_APPROVAL_EMAIL', None)
        
        if not admin_email:
            # Intentar obtener de ADMINS
            if hasattr(settings, 'ADMINS') and settings.ADMINS:
                admin_email = settings.ADMINS[0][1]
            else:
                return  # No hay email de admin configurado
        
        subject = f'[Fenix] Nuevo usuario pendiente de aprobación'
        
        # Construir enlace de aprobación
        approval_url = ''
        if request:
            from django.urls import reverse
            approval_url = request.build_absolute_uri(reverse('accounts:user_approval_dashboard'))
        
        message = f'Nuevo usuario registrado en Fenix:\n\n'
        message += f'Nombre: {user.full_name}\n'
        message += f'Email: {user.email}\n'
        message += f'Empresa: {user.company}\n'
        message += f'Fecha de registro: {user.date_joined.strftime("%d/%m/%Y %H:%M")}\n'
        message += f'Email verificado: {"Sí" if user.email_verified else "No"}\n\n'
        
        if approval_url:
            message += f'Revisar y aprobar: {approval_url}\n\n'
        
        message += 'Este usuario requiere aprobación para acceder al sistema.\n\n'
        message += 'Saludos,\nSistema Fenix'
        
        from_email = platform.email_from or settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [admin_email], fail_silently=True)
        
    except Exception as e:
        # Log el error pero no fallar el registro
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error sending admin notification: {e}')


def send_user_approved_email(user, request=None):
    """
    Envía email al usuario notificando que su cuenta ha sido aprobada.
    """
    try:
        platform = PlatformSettings.get_settings()
        lang = user.language or platform.default_language or 'es'
        
        # Construir URL de login
        login_url = ''
        if request:
            from django.urls import reverse
            login_url = request.build_absolute_uri(reverse('accounts:login'))
        
        if lang == 'zh-hans':
            subject = 'Fenix - 您的账户已获批准'
            message = f'您好 {user.full_name},\n\n'
            message += '好消息！您的 Fenix 账户已被批准。\n\n'
            message += '现在可以使用您的凭据登录平台了。\n\n'
            if login_url:
                message += f'登录链接：{login_url}\n\n'
            message += '欢迎来到 Fenix！\n\n'
            message += '此致，\nFenix 团队'
        else:
            subject = 'Fenix - Tu cuenta ha sido aprobada'
            message = f'Hola {user.full_name},\n\n'
            message += '¡Buenas noticias! Tu cuenta de Fenix ha sido aprobada.\n\n'
            message += 'Ya puedes iniciar sesión en la plataforma con tus credenciales.\n\n'
            if login_url:
                message += f'Iniciar sesión: {login_url}\n\n'
            message += '¡Bienvenido a Fenix!\n\n'
            message += 'Saludos,\nEquipo Fenix'
        
        from_email = platform.email_from or settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [user.email], fail_silently=False)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error sending approval email: {e}')
        raise


def send_user_rejected_email(user, request=None):
    """
    Envía email al usuario notificando que su solicitud ha sido rechazada.
    """
    try:
        platform = PlatformSettings.get_settings()
        lang = user.language or platform.default_language or 'es'
        
        if lang == 'zh-hans':
            subject = 'Fenix - 账户申请状态'
            message = f'您好 {user.full_name},\n\n'
            message += '感谢您对 Fenix 的关注。\n\n'
            message += '我们已审核您的申请，遗憾地通知您，目前我们无法批准您的账户。\n\n'
            message += '如有任何疑问，请联系我们的支持团队。\n\n'
            message += '此致，\nFenix 团队'
        else:
            subject = 'Fenix - Estado de solicitud de cuenta'
            message = f'Hola {user.full_name},\n\n'
            message += 'Gracias por tu interés en Fenix.\n\n'
            message += 'Hemos revisado tu solicitud y lamentablemente no podemos aprobar tu cuenta en este momento.\n\n'
            message += 'Si tienes alguna pregunta, por favor contacta a nuestro equipo de soporte.\n\n'
            message += 'Saludos,\nEquipo Fenix'
        
        from_email = platform.email_from or settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [user.email], fail_silently=False)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error sending rejection email: {e}')
        raise
