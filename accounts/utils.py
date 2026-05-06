"""
Utilidades para cuentas de usuario: tokens de verificación, helpers de roles, etc.
"""
import secrets
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _, gettext
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from core.models import PlatformSettings


def generate_email_verification_token():
    """Genera un token seguro para verificación de email"""
    return secrets.token_urlsafe(32)


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
    return gettext("¡%(greeting)s, %(name)s!") % {'greeting': greeting, 'name': name}


def is_manager_or_admin(user):
    """Helper para verificar si el usuario es Admin o Super Admin"""
    from accounts.models import User
    return (
        user.role in (User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN) or
        user.is_superuser or
        user.is_staff
    )


def get_dashboard_status(user):
    """
    Retorna información de estado GLOBAL del dashboard (no operativo).
    
    El HERO responde a: "¿Tengo algo urgente ahora mismo?"
    Las tarjetas responden a: "Si entro aquí, ¿qué veré?"
    
    Estados:
    - 🟢 OK (0 acciones): "Todo está en orden por ahora" + check-circle verde
    - 🟡 ATENCIÓN (1-2 acciones): "Tienes acciones pendientes" + alert-circle amarillo
    - 🔴 URGENTE (críticas): "Requiere atención inmediata" + alert-octagon rojo
    
    Returns:
        dict: {
            'message': str,
            'level': str ('success', 'warning', 'danger'),
            'icon': str (nombre del icono SVG)
        }
    """
    from orders.models import Order
    from notifications.models import Notification
    
    try:
        pending_count = 0
        has_urgent = False
        
        # Contar acciones pendientes
        if user.has_perm('orders.view_order'):
            pending_orders = Order.objects.filter(status='pending').count()
            pending_count += pending_orders
            # Los pedidos pendientes de más de X días serían urgentes (ejemplo)
            # Por ahora consideramos urgente si hay más de 5 pedidos
            if pending_orders > 5:
                has_urgent = True
        
        if hasattr(user, 'notifications'):
            unread = Notification.objects.filter(user=user, read=False).count()
            pending_count += unread
            # Notificaciones prioritarias serían urgentes
            urgent_notifications = Notification.objects.filter(
                user=user, read=False, priority='high'
            ).exists() if hasattr(Notification, 'priority') else False
            if urgent_notifications:
                has_urgent = True
        
        # 🔴 ESTADO URGENTE - acciones críticas
        if has_urgent:
            return {
                'message': gettext("Requiere atención inmediata"),
                'level': 'danger',
                'icon': 'alert-octagon'
            }
        
        # 🟡 ESTADO ATENCIÓN - hay acciones pendientes
        if pending_count > 0:
            return {
                'message': gettext("Tienes acciones pendientes"),
                'level': 'warning',
                'icon': 'alert-circle'
            }
        
        # 🟢 ESTADO OK - todo en orden
        return {
            'message': gettext("Todo está en orden por ahora"),
            'level': 'success',
            'icon': 'check-circle'
        }
    except Exception:
        # Fallback seguro - estado OK por defecto
        return {
            'message': gettext("Plataforma operativa"),
            'level': 'success',
            'icon': 'check-circle'
        }


def send_verification_email(user, verification_url):
    """
    Envía email de verificación al usuario con enlace de confirmación.
    Usa plantillas HTML/Text y i18n a través del sistema de templates.
    """
    from .models import EmailVerificationToken
    from django.core.mail import EmailMultiAlternatives
    from django.utils import translation
    
    platform = PlatformSettings.get_settings()
    lang = user.language or platform.default_language or 'es'
    
    # Crear token de verificación
    token = EmailVerificationToken.objects.create(user=user)
    verification_link = f"{verification_url}?token={token.token}"
    
    # Activar idioma del usuario para el renderizado
    with translation.override(lang):
        context = {
            'user': user,
            'verification_link': verification_link,
            'platform': platform,
        }
        
        subject = render_to_string('accounts/emails/email_verification_subject.txt', context).strip()
        html_content = render_to_string('accounts/emails/email_verification.html', context)
        text_content = strip_tags(html_content)
    
    from_email = platform.email_from or settings.DEFAULT_FROM_EMAIL
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


def send_approval_notification(user, approved=True):
    """
    Envía notificación al usuario cuando su cuenta es aprobada/rechazada.
    Redirige a las funciones específicas de envío.
    """
    if approved:
        send_user_approved_email(user)
    else:
        send_user_rejected_email(user)


def send_user_approved_email(user, request=None):
    """
    Envía email al usuario notificando que su cuenta ha sido aprobada.
    """
    from django.core.mail import EmailMultiAlternatives
    from django.utils import translation
    from django.urls import reverse
    
    try:
        platform = PlatformSettings.get_settings()
        lang = user.language or platform.default_language or 'es'
        
        # Construir URL de login
        login_url = ''
        if request:
            login_url = request.build_absolute_uri(reverse('accounts:login'))
        else:
            # Fallback si no hay request (ej. desde celery o admin save)
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            login_url = f"{site_url}{reverse('accounts:login')}"
        
        with translation.override(lang):
            context = {
                'user': user,
                'login_url': login_url,
                'platform': platform,
            }
            
            subject = render_to_string('accounts/emails/user_approved_subject.txt', context).strip()
            html_content = render_to_string('accounts/emails/user_approved.html', context)
            text_content = strip_tags(html_content)
        
        from_email = platform.email_from or settings.DEFAULT_FROM_EMAIL
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error sending approval email: {e}')
        if request:
            raise
        # Si no hay request, no propagamos para no romper el guardado en admin


def send_user_rejected_email(user, request=None):
    """
    Envía email al usuario notificando que su solicitud ha sido rechazada.
    """
    from django.core.mail import EmailMultiAlternatives
    from django.utils import translation
    
    try:
        platform = PlatformSettings.get_settings()
        lang = user.language or platform.default_language or 'es'
        
        with translation.override(lang):
            context = {
                'user': user,
                'platform': platform,
            }
            
            subject = render_to_string('accounts/emails/user_rejected_subject.txt', context).strip()
            html_content = render_to_string('accounts/emails/user_rejected.html', context)
            text_content = strip_tags(html_content)
        
        from_email = platform.email_from or settings.DEFAULT_FROM_EMAIL
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error sending rejection email: {e}')
        if request:
            raise
