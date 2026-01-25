from django.db import models


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
        return obj
