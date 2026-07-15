from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import LoginHistory, ProfileAuditLog, UserSession
from ai_assistant.models import AILead
from core.audit import AuditLog
from core.models import ContactLead, RateLimitBucket
from crm.models import CRMLead
from whatsapp.models import WhatsAppLead


class Command(BaseCommand):
    help = 'Aplica la política de retención. Por defecto sólo muestra el impacto.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Ejecuta las eliminaciones')

    def handle(self, *args, **options):
        now = timezone.now()
        contact_cutoff = now - timedelta(days=settings.DATA_RETENTION_CONTACT_DAYS)
        security_cutoff = now - timedelta(days=settings.DATA_RETENTION_SECURITY_DAYS)
        audit_cutoff = now - timedelta(days=settings.DATA_RETENTION_AUDIT_DAYS)
        candidates = {
            'sesiones Django expiradas': Session.objects.filter(expire_date__lt=now),
            'contadores de rate limit': RateLimitBucket.objects.filter(expires_at__lt=now),
            'sesiones de usuario expiradas': UserSession.objects.filter(expires_at__lt=now),
            'historial de login': LoginHistory.objects.filter(created_at__lt=security_cutoff),
            'auditoría de perfil': ProfileAuditLog.objects.filter(created_at__lt=audit_cutoff),
            'auditoría operativa': AuditLog.objects.filter(created_at__lt=audit_cutoff),
            'leads IA no verificados': AILead.objects.filter(email_verified=False, updated_at__lt=now - timedelta(days=30)),
            'leads IA inactivos': AILead.objects.filter(email_verified=True, updated_at__lt=contact_cutoff),
            'contactos descartados': ContactLead.objects.filter(estado=ContactLead.STATUS_DISCARDED, updated_at__lt=contact_cutoff),
            'CRM descartado': CRMLead.objects.filter(validation_status=CRMLead.VALIDATION_DESCARTADO, updated_at__lt=contact_cutoff),
            'leads WhatsApp antiguos': WhatsAppLead.objects.filter(created_at__lt=contact_cutoff),
        }
        total = 0
        for label, queryset in candidates.items():
            count = queryset.count()
            total += count
            self.stdout.write(f'{label}: {count}')
            if options['apply'] and count:
                queryset.delete()
        mode = 'ELIMINADOS' if options['apply'] else 'CANDIDATOS (dry-run)'
        self.stdout.write(self.style.SUCCESS(f'{mode}: {total}'))
