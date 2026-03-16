from django.db import models
from django.utils.translation import gettext_lazy as _

class WhatsAppLead(models.Model):
    """
    Modelo para registrar las solicitudes de contacto por WhatsApp.
    """
    name = models.CharField(_("Nombre"), max_length=100)
    message = models.TextField(_("Mensaje"))
    page_url = models.URLField(_("URL de la página"), max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)
    sent_successfully = models.BooleanField(_("Enviado correctamente"), default=False)
    api_response = models.JSONField(_("Respuesta de la API"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lead de WhatsApp")
        verbose_name_plural = _("Leads de WhatsApp")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
