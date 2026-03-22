import os
from django.conf import settings

def whatsapp_context(request):
    """
    Expose WhatsApp configuration to templates.
    """
    # Intentar obtener de settings o directamente del env
    phone = getattr(settings, 'WHATSAPP_PHONE', os.getenv('DEFAULT_WHATSAPP_TARGET', '34624149250'))
    
    return {
        'WHATSAPP_PHONE': phone,
    }
