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
                'plataformafenix2026@gmail.com',
            )
            obj.save(update_fields=['order_notification_email'])
        return obj


# AuditLog model is now imported from audit.py
__all__ = ['PlatformSettings', 'AuditLog']
