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
    Si pending_approval=True, redirige a una página de espera (excepto Super Admin/Manager).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # El LocaleMiddleware ya maneja el idioma desde cookie/sesión
        # Solo establecemos el idioma del usuario si no hay idioma en sesión/cookie
        # y el usuario está autenticado con preferencia de idioma
        if request.user.is_authenticated and not request.session.get('django_language'):
            lang = get_user_language(request.user)
            if lang and lang != 'es':  # Solo si es diferente del default
                translation.activate(lang)
                request.session['django_language'] = lang
        
        # Rutas que no requieren aprobación
        allowed_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/register/',
            '/admin/',
        ]
        
        # Si el usuario está autenticado y no es Super Admin/Manager
        if request.user.is_authenticated:
            user = request.user
            is_admin = is_manager_or_admin(user)
            
            # Si está pendiente de aprobación y no es admin, bloquear acceso
            if user.pending_approval and not is_admin:
                # Permitir acceso a logout y profile (para ver estado)
                if request.path not in allowed_paths and not request.path.startswith('/accounts/profile'):
                    messages.warning(
                        request,
                        _('Tu cuenta está pendiente de aprobación. Un administrador revisará tu solicitud.')
                    )
                    return redirect('accounts:profile')
        
        response = self.get_response(request)
        return response
