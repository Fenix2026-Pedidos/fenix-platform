"""
Context processors para accounts app.
Añade información del usuario y configuración de idioma al contexto global.
"""
from django.utils import translation
from core.models import PlatformSettings
from .utils import get_user_language, get_time_based_greeting, get_user_greeting, get_dashboard_status


def user_language(request):
    """
    Context processor que proporciona información del idioma del usuario.
    El LocaleMiddleware ya maneja la activación del idioma desde cookie/sesión.
    Este processor solo proporciona información adicional al contexto.
    """
    from django.utils.translation import get_language
    
    # Obtener idioma actual (ya activado por LocaleMiddleware)
    current_lang = get_language()
    
    # Si no hay idioma en sesión/cookie y el usuario tiene preferencia, sugerirla
    user_lang = None
    if request.user.is_authenticated:
        user_lang = get_user_language(request.user)
    
    return {
        'user_lang': user_lang or current_lang,
        'LANGUAGE_CODE': current_lang,
    }


def user_greeting(request):
    """
    Context processor que proporciona saludo inteligente según hora del día.
    Disponible en todos los templates como {{ user_greeting }} y {{ dashboard_status }}.
    """
    if not request.user.is_authenticated:
        return {
            'time_greeting': '',
            'user_greeting': '',
            'dashboard_status': None,
        }
    
    return {
        'time_greeting': get_time_based_greeting(),
        'user_greeting': get_user_greeting(request.user),
        'dashboard_status': get_dashboard_status(request.user),
    }
