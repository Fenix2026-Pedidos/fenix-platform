import logging
import time
import os
from django.conf import settings

logger = logging.getLogger('audit')

class AuditLogMiddleware:
    """
    Middleware de Auditoría de Synerg-IA.
    Registra cada petición para trazabilidad de seguridad y rendimiento.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Asegurar que el directorio de logs existe
        self.log_dir = os.path.join(settings.BASE_DIR, 'logs')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def __call__(self, request):
        start_time = time.time()
        
        # Información de la petición
        ip = self.get_client_ip(request)
        user = request.user if request.user.is_authenticated else "Anonymous"
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        status_code = response.status_code
        
        # Log entry
        log_msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {ip} - {user} - {request.method} {request.path} - {status_code} ({duration:.2f}s)"
        
        # Escribir en archivo de auditoría
        with open(os.path.join(self.log_dir, 'audit.log'), 'a') as f:
            f.write(log_msg + "\n")
            
        # Añadir cabecera de seguridad Synerg-IA
        response['X-SynergIA-Shield'] = 'Active-v1'
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
