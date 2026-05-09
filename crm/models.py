import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class CRMLead(models.Model):
    """
    Modelo de Lead Unificado para el CRM Omnicanal de Fenix.
    """
    CHANNEL_WEB_ASSISTANT = 'web_assistant'
    CHANNEL_WHATSAPP = 'whatsapp'
    CHANNEL_CONTACT_FORM = 'contact_form'
    CHANNEL_MANUAL = 'manual'

    CHANNEL_CHOICES = [
        (CHANNEL_WEB_ASSISTANT, _('Asistente Web')),
        (CHANNEL_WHATSAPP, _('WhatsApp')),
        (CHANNEL_CONTACT_FORM, _('Formulario de Contacto')),
        (CHANNEL_MANUAL, _('Manual')),
    ]

    STATUS_NUEVO = 'nuevo'
    STATUS_PENDIENTE = 'pendiente'
    STATUS_CONTACTADO = 'contactado'
    STATUS_PRESUPUESTO = 'presupuesto_enviado'
    STATUS_CONVERTIDO = 'convertido'
    STATUS_PERDIDO = 'perdido'
    STATUS_SIN_RESPUESTA = 'sin_respuesta'

    STATUS_CHOICES = [
        (STATUS_NUEVO, _('Nuevo')),
        (STATUS_PENDIENTE, _('Pendiente')),
        (STATUS_CONTACTADO, _('Contactado')),
        (STATUS_PRESUPUESTO, _('Presupuesto Enviado')),
        (STATUS_CONVERTIDO, _('Convertido')),
        (STATUS_PERDIDO, _('Perdido')),
        (STATUS_SIN_RESPUESTA, _('Sin Respuesta')),
    ]

    VALIDATION_NUEVO = 'nuevo'
    VALIDATION_VALIDADO = 'validado'
    VALIDATION_ATENDIDO = 'atendido'
    VALIDATION_DESCARTADO = 'descartado'

    VALIDATION_CHOICES = [
        (VALIDATION_NUEVO, _('Nuevo')),
        (VALIDATION_VALIDADO, _('Validado')),
        (VALIDATION_ATENDIDO, _('Atendido')),
        (VALIDATION_DESCARTADO, _('Descartado/Spam')),
    ]

    PRIORITY_ALTA = 'alta'
    PRIORITY_MEDIA = 'media'
    PRIORITY_BAJA = 'baja'

    PRIORITY_CHOICES = [
        (PRIORITY_ALTA, _('Alta')),
        (PRIORITY_MEDIA, _('Media')),
        (PRIORITY_BAJA, _('Baja')),
    ]

    # IDENTIFICACIÓN ÚNICA
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # INFORMACIÓN DE CONTACTO
    full_name = models.CharField(_("Nombre Completo"), max_length=255)
    company_name = models.CharField(_("Empresa"), max_length=255, blank=True, null=True)
    phone = models.CharField(_("Teléfono"), max_length=50, blank=True, null=True, db_index=True)
    email = models.EmailField(_("Correo Electrónico"), blank=True, null=True, db_index=True)

    # CANAL DE ENTRADA Y ORIGEN DETALLADO
    channel = models.CharField(_("Canal"), max_length=30, choices=CHANNEL_CHOICES, default=CHANNEL_WEB_ASSISTANT)
    source = models.CharField(_("Origen Detallado"), max_length=255, blank=True, null=True, help_text="Ej: Fenix Assistant (OTP), WhatsApp Web Form, etc.")
    first_message = models.TextField(_("Primer Mensaje"), blank=True, null=True)

    # ESTADOS Y CONTROL COMERCIAL
    lead_status = models.CharField(_("Estado Comercial"), max_length=30, choices=STATUS_CHOICES, default=STATUS_NUEVO)
    validation_status = models.CharField(_("Estado de Validación"), max_length=30, choices=VALIDATION_CHOICES, default=VALIDATION_NUEVO)
    priority = models.CharField(_("Prioridad"), max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIA)
    
    # ASIGNACIÓN Y VALOR COMERCIAL
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_crm_leads',
        verbose_name=_("Asignado a")
    )
    estimated_value = models.DecimalField(_("Valor Estimado (€)"), max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(_("Notas Comerciales"), blank=True, null=True)
    geographic_zone = models.CharField(_("Zona Geográfica"), max_length=150, blank=True, null=True, help_text="Ej: Madrid, Barcelona, Toledo...")

    # CONTROL DE TIEMPOS
    last_contact_at = models.DateTimeField(_("Último Contacto"), default=timezone.now)
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Última Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Lead de CRM")
        verbose_name_plural = _("Leads de CRM")
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_serial_id()}] {self.full_name} ({self.get_channel_display()})"

    @property
    def serial_id(self):
        """Retorna el ID numérico formateado como consecutivo serial."""
        return f"#{str(self.id).zfill(4)}"

    def get_serial_id(self):
        """Método helper para plantillas."""
        return self.serial_id

    def get_status_badge_class(self):
        """Clase CSS correspondiente para el estado comercial."""
        classes = {
            self.STATUS_NUEVO: 'bg-info text-white',
            self.STATUS_PENDIENTE: 'bg-warning text-dark',
            self.STATUS_CONTACTADO: 'bg-primary text-white',
            self.STATUS_PRESUPUESTO: 'bg-secondary text-white',
            self.STATUS_CONVERTIDO: 'bg-success text-white',
            self.STATUS_PERDIDO: 'bg-danger text-white',
            self.STATUS_SIN_RESPUESTA: 'bg-dark text-white',
        }
        return classes.get(self.lead_status, 'bg-light text-dark')

    def get_validation_badge_class(self):
        """Clase CSS correspondiente para el estado de validación."""
        classes = {
            self.VALIDATION_NUEVO: 'bg-info text-white',
            self.VALIDATION_VALIDADO: 'bg-success text-white',
            self.VALIDATION_ATENDIDO: 'bg-primary text-white',
            self.VALIDATION_DESCARTADO: 'bg-danger text-white',
        }
        return classes.get(self.validation_status, 'bg-light text-dark')

    def get_priority_badge_class(self):
        """Clase CSS correspondiente para la prioridad."""
        classes = {
            self.PRIORITY_ALTA: 'bg-danger text-white',
            self.PRIORITY_MEDIA: 'bg-warning text-dark',
            self.PRIORITY_BAJA: 'bg-info text-white',
        }
        return classes.get(self.priority, 'bg-light text-dark')


class CRMLeadMessage(models.Model):
    """
    Modelo de Mensaje/Interacción para registrar el historial completo de un Lead.
    """
    SENDER_LEAD = 'lead'
    SENDER_AGENT = 'agent'
    SENDER_SYSTEM = 'system'
    SENDER_AI = 'ai'

    SENDER_CHOICES = [
        (SENDER_LEAD, _('Lead')),
        (SENDER_AGENT, _('Agente Comercial')),
        (SENDER_SYSTEM, _('Sistema')),
        (SENDER_AI, _('Asistente IA')),
    ]

    lead = models.ForeignKey(
        CRMLead,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Lead")
    )
    
    # Canal a través del cual ocurrió esta interacción específica
    channel = models.CharField(_("Canal"), max_length=30, choices=CRMLead.CHANNEL_CHOICES)
    sender = models.CharField(_("Remitente"), max_length=20, choices=SENDER_CHOICES, default=SENDER_LEAD)
    message = models.TextField(_("Mensaje / Nota / Acción"))
    timestamp = models.DateTimeField(_("Fecha y Hora"), default=timezone.now, db_index=True)
    metadata = models.JSONField(_("Metadatos Adicionales"), blank=True, null=True, help_text="Estructura flexible para guardar payloads de webhook, etc.")

    class Meta:
        verbose_name = _("Mensaje de Lead")
        verbose_name_plural = _("Historial de Mensajes")
        ordering = ['timestamp']

    def __str__(self):
        return f"Mensaje de {self.get_sender_display()} para Lead #{self.lead.id} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
