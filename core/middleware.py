import logging
import time
import os
from django.conf import settings
from core.rate_limit import client_ip

logger = logging.getLogger('audit')


class SecurityHeadersMiddleware:
    """Cabeceras defensivas compatibles con la interfaz actual."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.setdefault('X-Permitted-Cross-Domain-Policies', 'none')
        # Report-Only permite medir antes de retirar los scripts inline.
        response.setdefault(
            'Content-Security-Policy-Report-Only',
            "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'self'; "
            "form-action 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://flagcdn.com https://storage.googleapis.com; "
            "connect-src 'self'; font-src 'self' data: https://cdn.jsdelivr.net",
        )
        return response

class AuditLogMiddleware:
    """
    Middleware de Auditoría de Synerg-IA.
    Registra cada petición para trazabilidad de seguridad y rendimiento.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Asegurar que el directorio de logs existe si es escribible
        self.log_dir = os.path.join(settings.BASE_DIR, 'logs')
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
        except OSError:
            pass

    def __call__(self, request):
        start_time = time.time()
        
        # Información de la petición
        ip = self.get_client_ip(request)
        user = f'user:{request.user.pk}' if request.user.is_authenticated else "anonymous"
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        status_code = response.status_code
        
        # Log entry
        log_msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {ip} - {user} - {request.method} {request.path} - {status_code} ({duration:.2f}s)"
        
        # Escribir en archivo de auditoría si es posible; si no (ej: App Engine), usar logger
        if settings.DEBUG:
            try:
                with open(os.path.join(self.log_dir, 'audit.log'), 'a', encoding='utf-8') as f:
                    f.write(log_msg + "\n")
            except OSError:
                logger.info(log_msg)
        else:
            logger.info(log_msg)
            
        # Añadir cabecera de seguridad Synerg-IA
        response['X-SynergIA-Shield'] = 'Active-v1'
        
        return response

    def get_client_ip(self, request):
        return client_ip(request)
