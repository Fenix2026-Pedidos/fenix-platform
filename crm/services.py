import logging
import threading
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from core.models import PlatformSettings
from .models import CRMLead, CRMLeadMessage

logger = logging.getLogger(__name__)

class CRMLeadService:
    """
    Servicio unificado para la gestión de Leads e Historial de Mensajes.
    """

    @staticmethod
    def log_lead(channel, full_name, email=None, phone=None, company_name=None, message=None, source=None, geographic_zone=None, metadata=None):
        """
        Registra o actualiza un Lead en la base de datos del CRM.
        Si ya existe un lead con el mismo teléfono (o email), no crea uno nuevo sino que actualiza
        el campo de último contacto y añade el mensaje al historial.
        
        Retorna:
            (lead, created) -> Tuple[CRMLead, bool]
        """
        lead = None
        created = False
        
        # Limpiar datos
        email = email.strip() if email else None
        phone = phone.strip() if phone else None
        full_name = full_name.strip() if full_name else "Contacto CRM"
        company_name = company_name.strip() if company_name else None
        source = source.strip() if source else None
        geographic_zone = geographic_zone.strip() if geographic_zone else None

        # 1. Buscar duplicados (Por teléfono o por email)
        if phone:
            # Buscar coincidencia exacta de teléfono
            lead = CRMLead.objects.filter(phone=phone).first()
        elif email:
            # Buscar coincidencia exacta de email
            lead = CRMLead.objects.filter(email=email).first()

        # 2. Si existe, actualizar marcas de tiempo e historial
        if lead:
            lead.last_contact_at = timezone.now()
            
            # Si el canal original era más básico, o para mantener consistencia, podemos conservar info
            if geographic_zone and not lead.geographic_zone:
                lead.geographic_zone = geographic_zone
            if company_name and not lead.company_name:
                lead.company_name = company_name
            
            lead.save(update_fields=['last_contact_at', 'geographic_zone', 'company_name', 'updated_at'])
            
            if message:
                # Registrar mensaje entrante de este lead
                CRMLeadMessage.objects.create(
                    lead=lead,
                    channel=channel,
                    sender=CRMLeadMessage.SENDER_LEAD,
                    message=message,
                    metadata=metadata
                )
        else:
            # 3. Si no existe, crear un nuevo lead automáticamente
            lead = CRMLead.objects.create(
                full_name=full_name,
                email=email,
                phone=phone,
                company_name=company_name,
                channel=channel,
                source=source,
                first_message=message,
                lead_status=CRMLead.STATUS_NUEVO,
                validation_status=CRMLead.VALIDATION_NUEVO,
                geographic_zone=geographic_zone,
                last_contact_at=timezone.now()
            )
            created = True
            
            if message:
                CRMLeadMessage.objects.create(
                    lead=lead,
                    channel=channel,
                    sender=CRMLeadMessage.SENDER_LEAD,
                    message=message,
                    metadata=metadata
                )
            
            # 4. Enviar notificación interna en segundo plano para no demorar la respuesta de cara al cliente
            threading.Thread(target=send_crm_lead_notification, args=(lead,)).start()

        # Sincronizar opcionalmente con Google Sheets en segundo plano
        if getattr(settings, 'GOOGLE_SHEETS_WEBHOOK_URL', None):
            threading.Thread(target=sync_to_sheets_backup, args=(lead, message or "Registro CRM")).start()

        return lead, created

    @staticmethod
    def log_message(lead, channel, sender, message, metadata=None):
        """
        Agrega un mensaje de interacción al historial de un Lead específico.
        """
        if not lead or not message:
            return None

        # Actualizar último contacto del lead
        lead.last_contact_at = timezone.now()
        lead.save(update_fields=['last_contact_at', 'updated_at'])

        # Crear el mensaje de historial
        return CRMLeadMessage.objects.create(
            lead=lead,
            channel=channel,
            sender=sender,
            message=message,
            metadata=metadata
        )


def send_crm_lead_notification(lead):
    """
    Envía un email HTML premium al administrador del sistema sobre un nuevo lead en el CRM.
    """
    try:
        ps = PlatformSettings.get_settings()
        subject = f"[{ps.email_from_name}] ¡Nuevo Lead CRM Omnicanal! ({lead.get_channel_display()}) - {lead.serial_id}"
        
        # Plantilla premium HTML
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="background-color: #8b5e3c; color: white; padding: 15px; border-radius: 6px 6px 0 0; text-align: center;">
                <h2 style="margin: 0; font-size: 20px; letter-spacing: 0.5px;">¡Nuevo Lead Capturado! {lead.serial_id}</h2>
            </div>
            <div style="padding: 20px; background-color: #fafafa;">
                <p style="font-size: 15px; margin-top: 0;">Se ha registrado un nuevo lead en la base de datos comercial del CRM de Fenix:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; width: 35%; color: #555;">ID Consecutivo:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; color: #8b5e3c;">{lead.serial_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; color: #555;">Nombre Completo:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{lead.full_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; color: #555;">Canal de Origen:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; color: #2563eb; font-weight: bold;">{lead.get_channel_display()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; color: #555;">Zona Geográfica:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; color: #16a34a;">{lead.geographic_zone or 'No especificada'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; color: #555;">Teléfono:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{lead.phone or 'No especificado'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; color: #555;">Email:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{lead.email or 'No especificado'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; color: #555;">Origen Detallado:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-style: italic;">{lead.source or 'No especificado'}</td>
                    </tr>
                </table>
                <p style="font-weight: bold; color: #555; margin-bottom: 5px;">Mensaje Inicial:</p>
                <blockquote style="background: #ffffff; border-left: 4px solid #8b5e3c; padding: 12px 15px; margin: 0 0 20px 0; font-style: italic; border-radius: 0 4px 4px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    {lead.first_message or 'Sin mensaje de texto inicial.'}
                </blockquote>
                <div style="text-align: center; margin: 25px 0 10px 0;">
                    <a href="https://fenixdelamancha.es/crm/leads/{lead.uuid}/" style="background-color: #8b5e3c; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; box-shadow: 0 2px 4px rgba(139,94,60,0.3); font-size: 14px;">Gestionar en el CRM de Fenix</a>
                </div>
            </div>
            <div style="background-color: #eaeaea; padding: 12px; border-radius: 0 0 6px 6px; text-align: center; font-size: 11px; color: #666;">
                Este es un aviso automático generado por la Plataforma Fenix. No responda a este email.
            </div>
        </body>
        </html>
        """
        recipient = ps.order_notification_email or 'distribuciones722@gmail.com'
        from_email = f'{ps.email_from_name} <{ps.email_from}>'
        
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[recipient],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
        logger.info(f"[CRM NOTIFICACIÓN] Email de lead {lead.serial_id} enviado a {recipient}")
        return True
    except Exception as e:
        logger.error(f"[CRM NOTIFICACIÓN] Error enviando email de lead {lead.id}: {e}", exc_info=True)
        return False


def sync_to_sheets_backup(lead, message):
    """
    Sincronización en segundo plano con el Webhook de Google Sheets como respaldo analítico.
    """
    import requests
    import json
    webhook_url = getattr(settings, 'GOOGLE_SHEETS_WEBHOOK_URL', None)
    if not webhook_url:
        return False

    try:
        payload = {
            "source": f"CRM: {lead.get_channel_display()} ({lead.source or 'Direct'})",
            "name": lead.full_name,
            "email": lead.email or "-",
            "phone_prefix": "",
            "phone_number": lead.phone or "-",
            "company": lead.company_name or "-",
            "message": f"[{lead.serial_id}] {message}"
        }
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"[CRM BACKUP] Lead {lead.serial_id} sincronizado correctamente con Google Sheets.")
            return True
    except Exception as e:
        logger.warning(f"[CRM BACKUP] Ocurrió un error al enviar respaldo a Google Sheets: {e}")
    return False
