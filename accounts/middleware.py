"""
Middleware para controlar el acceso según el estado del usuario.
Bloquea el acceso si el usuario tiene pending_approval=True (excepto para Super Admin/Manager).
También establece el idioma del usuario según su preferencia.
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from .utils import get_user_language, is_manager_or_admin


class UserApprovalMiddleware:
    """
    Middleware que verifica si el usuario está aprobado.
    BLOQUEA acceso si:
    - email_verified != True  O
    - status != ACTIVE
    
    Redirige a page de "pending approval" (excepto admins que pueden ver admin panel).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # El LocaleMiddleware ya maneja el idioma desde cookie/sesión
        if request.user.is_authenticated and not request.session.get('django_language'):
            lang = get_user_language(request.user)
            if lang and lang != 'es':
                translation.activate(lang)
                request.session['django_language'] = lang
        
        # Rutas que SIEMPRE están permitidas (no requieren aprobación)
        public_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/register/',
            '/accounts/verify-email/',
            '/accounts/pending-approval/',
            '/accounts/email-verification/',
            '/admin/',
        ]
        
        # Si el usuario está autenticado
        if request.user.is_authenticated:
            user = request.user
            from accounts.models import User
            
            # GATE DE SEGURIDAD: Verificar que tenga email verificado Y status ACTIVE
            needs_approval = (
                not user.email_verified or 
                user.status != User.STATUS_ACTIVE
            )
            
            if needs_approval:
                # Admin/Super Admin solo pueden ver admin panel, nada más
                is_admin = user.is_staff or user.role in ('admin', 'super_admin')
                
                # Si es admin y está en /admin/, permitir
                if is_admin and request.path.startswith('/admin/'):
                    return self.get_response(request)
                
                # Si el path NO está en la lista de rutas públicas, bloquear
                if not any(request.path.startswith(p) for p in public_paths):
                    messages.warning(
                        request,
                        _('Tu cuenta está pendiente de aprobación. Un administrador revisará tu solicitud.')
                    )
                    return redirect('accounts:pending_approval')
        
        response = self.get_response(request)
        return response


class SessionTrackingMiddleware:
    """
    Middleware para tracking de sesiones y registro de actividad
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            from accounts.models import UserSession, LoginHistory
            from user_agents import parse
            from django.utils import timezone
            import datetime
            
            session_key = request.session.session_key
            
            if session_key:
                # Actualizar o crear sesión
                user_agent_string = request.META.get('HTTP_USER_AGENT', '')
                user_agent = parse(user_agent_string)
                ip_address = self.get_client_ip(request)
                
                # Device type
                if user_agent.is_mobile:
                    device_type = 'mobile'
                elif user_agent.is_tablet:
                    device_type = 'tablet'
                else:
                    device_type = 'desktop'
                
                # Actualizar o crear sesión
                session, created = UserSession.objects.update_or_create(
                    session_key=session_key,
                    defaults={
                        'user': request.user,
                        'ip_address': ip_address,
                        'user_agent': user_agent_string,
                        'device_type': device_type,
                        'browser': user_agent.browser.family,
                        'os': user_agent.os.family,
                        'is_active': True,
                        'expires_at': timezone.now() + datetime.timedelta(hours=24),
                    }
                )
                
                # Actualizar último login en User
                if request.user.last_login_at is None or \
                   (timezone.now() - request.user.last_login_at).total_seconds() > 300:  # 5 minutos
                    request.user.last_login_at = timezone.now()
                    request.user.last_login_ip = ip_address
                    request.user.save(update_fields=['last_login_at', 'last_login_ip'])
                    
                    # Registrar en historial
                    LoginHistory.objects.create(
                        user=request.user,
                        success=True,
                        ip_address=ip_address,
                        user_agent=user_agent_string,
                    )
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
