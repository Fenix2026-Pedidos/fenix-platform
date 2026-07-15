from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# Import AuditLog from audit module to avoid duplication
from .audit import AuditLog


class PlatformSettings(models.Model):
    """Configuración global de la plataforma (single-tenant)"""
    LANGUAGE_ES = 'es'
    LANGUAGE_ZH_HANS = 'zh-hans'

    LANGUAGE_CHOICES = [
        (LANGUAGE_ES, 'Español'),
        (LANGUAGE_ZH_HANS, 'Chinese (Simplified)'),
    ]

    default_language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default=LANGUAGE_ES,
        help_text='Idioma por defecto de la plataforma (fallback)',
    )
    email_from = models.EmailField(
        default='noreply@fenix.com',
        help_text='Email remitente para notificaciones',
    )
    email_from_name = models.CharField(
        max_length=200,
        default='FENIX',
        help_text='Nombre del remitente',
    )
    order_notification_email = models.EmailField(
        blank=True,
        default='',
        help_text='Email que recibe las notificaciones automáticas de pedidos',
    )
    default_delivery_window_hours = models.PositiveIntegerField(
        default=24,
        help_text='Ventana de entrega por defecto (horas)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Platform Settings'
        verbose_name_plural = 'Platform Settings'

    def save(self, *args, **kwargs):
        # Solo permitir una instancia
        self.pk = 1
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return 'Platform Settings'

    @classmethod
    def get_settings(cls):
        """Obtener o crear la configuración única"""
        obj, _ = cls.objects.get_or_create(pk=1)
        if not obj.order_notification_email:
            obj.order_notification_email = getattr(
                settings,
                'DEFAULT_ORDER_NOTIFICATION_EMAIL',
                'distribuciones722@gmail.com',
            )
            obj.save(update_fields=['order_notification_email'])
        return obj



class ContactLead(models.Model):
    """Leads recibidos desde el formulario de contacto público"""
    STATUS_NEW = 'nuevo'
    STATUS_CONTACTED = 'contactado'
    STATUS_DISCARDED = 'descartado'

    STATUS_CHOICES = [
        (STATUS_NEW, _('Nuevo')),
        (STATUS_CONTACTED, _('Contactado')),
        (STATUS_DISCARDED, _('Descartado')),
    ]

    nombre_completo = models.CharField(max_length=255, verbose_name=_('Nombre completo'))
    empresa = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Empresa'))
    email = models.EmailField(verbose_name=_('Correo electrónico'))
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Teléfono'))
    asunto = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Asunto'))
    mensaje = models.TextField(verbose_name=_('Mensaje'))
    
    acepta_privacidad = models.BooleanField(default=False, verbose_name=_('Acepta política de privacidad'))
    acepta_comunicaciones = models.BooleanField(default=False, verbose_name=_('Acepta comunicaciones comerciales'))
    
    origen = models.CharField(max_length=100, default='formulario_contacto_web', verbose_name=_('Origen'))
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name=_('Estado'))
    
    ip = models.GenericIPAddressField(blank=True, null=True, verbose_name=_('Dirección IP'))
    user_agent = models.TextField(blank=True, null=True, verbose_name=_('User Agent'))
    metadata = models.JSONField(blank=True, null=True, verbose_name=_('Metadatos adicionales'))

    # Evidencia de consentimiento: fecha y texto/política aceptada.
    privacy_accepted_at = models.DateTimeField(blank=True, null=True)
    privacy_policy_version = models.CharField(max_length=32, blank=True)
    marketing_consent_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Última actualización'))

    class Meta:
        verbose_name = _('Lead de contacto')
        verbose_name_plural = _('Leads de contacto')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['email']),
            models.Index(fields=['estado']),
        ]

    def __str__(self) -> str:
        return f"{self.nombre_completo} ({self.email}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class RateLimitBucket(models.Model):
    """Contador global de abuso, compartido por todas las instancias."""
    key = models.CharField(max_length=160, unique=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = 'Rate limit bucket'


class PrivacyRequest(models.Model):
    TYPE_ACCESS = 'access'
    TYPE_ERASURE = 'erasure'
    TYPE_RECTIFICATION = 'rectification'
    TYPE_CHOICES = [
        (TYPE_ACCESS, 'Acceso/portabilidad'),
        (TYPE_ERASURE, 'Supresión'),
        (TYPE_RECTIFICATION, 'Rectificación'),
    ]
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_COMPLETED, 'Completada'),
        (STATUS_REJECTED, 'Rechazada motivadamente'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(db_index=True)
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


# AuditLog model is imported from audit.py to avoid duplication.
__all__ = [
    'PlatformSettings',
    'AuditLog',
    'ContactLead',
    'RateLimitBucket',
    'PrivacyRequest',
]
