"""
Context processors para accounts app.
Añade información del usuario y configuración de idioma al contexto global.
"""
from django.utils import translation
from core.models import PlatformSettings
from .utils import get_user_language


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
