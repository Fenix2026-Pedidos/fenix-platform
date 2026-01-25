"""
Utilidades para cuentas de usuario: tokens de verificación, helpers de roles, etc.
"""
import secrets
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
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


def generate_email_verification_token():
    """Genera un token seguro para verificación de email"""
    return secrets.token_urlsafe(32)


def send_verification_email(user):
    """
    Envía email de verificación al usuario.
    Usa i18n según user.language -> platform.default_language -> es
    """
    platform = PlatformSettings.get_settings()
    lang = user.language or platform.default_language or 'es'
    
    # TODO: Implementar token en modelo User o tabla separada
    # Por ahora, solo enviamos un email informativo
    
    if lang == 'zh-hans':
        subject = 'FENIX - 请验证您的电子邮件'
        message = f'您好 {user.full_name},\n\n'
        message += '感谢您注册 FENIX。\n\n'
        message += '您的账户正在等待管理员批准。批准后，您将收到通知。\n\n'
        message += '此致，\nFENIX 团队'
    else:
        subject = 'FENIX - Verifica tu email'
        message = f'Hola {user.full_name},\n\n'
        message += 'Gracias por registrarte en FENIX.\n\n'
        message += 'Tu cuenta está pendiente de aprobación por un administrador. '
        message += 'Recibirás una notificación una vez que tu cuenta sea aprobada.\n\n'
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
    """Helper para verificar si el usuario es Manager o Super Admin"""
    return (
        user.role in (user.ROLE_SUPER_ADMIN, user.ROLE_MANAGER) or
        user.is_superuser or
        user.is_staff
    )
