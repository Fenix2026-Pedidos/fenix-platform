import json
import logging
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_POST

from core.rate_limit import client_ip, rate_limited
from crm.models import CRMLead
from crm.services import CRMLeadService
from .models import AILead
from .services import AIService

logger = logging.getLogger(__name__)


def _json_body(request):
    try:
        return json.loads(request.body or b'{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def session_status(request):
    if request.user.is_authenticated:
        return JsonResponse({'verified': True, 'authenticated': True})
    lead_id = request.session.get('ai_verified_lead_id')
    verified = AILead.objects.filter(pk=lead_id, email_verified=True).exists()
    return JsonResponse({'verified': verified, 'authenticated': False})


@require_POST
def capture_lead(request):
    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    name = str(data.get('name', '')).strip()[:255]
    email = str(data.get('email', '')).strip().lower()
    phone_prefix = str(data.get('phone_prefix', '+34')).strip()[:10]
    phone_number = str(data.get('phone_number', '')).strip()
    privacy_accepted = data.get('privacy_accepted') is True

    if rate_limited(request, 'ai-capture-ip', 5, 15 * 60):
        return JsonResponse({'error': 'Demasiadas solicitudes. Inténtalo más tarde.'}, status=429)
    if email and rate_limited(request, 'ai-capture-email', 3, 15 * 60, email):
        return JsonResponse({'error': 'Espera antes de solicitar otro código.'}, status=429)

    if not all([name, email, phone_number, privacy_accepted]):
        return JsonResponse({'error': 'Faltan campos obligatorios.'}, status=400)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'El correo electrónico no es válido.'}, status=400)

    clean_phone = re.sub(r'[\s\-()]+', '', phone_number)
    pattern = r'^[6789]\d{8}$' if phone_prefix == '+34' else r'^\d{7,15}$'
    if not re.fullmatch(pattern, clean_phone):
        return JsonResponse({'error': 'El número de teléfono no es válido.'}, status=400)

    now = timezone.now()
    lead = AILead.objects.filter(email=email).first()
    if lead and lead.otp_last_sent_at and now - lead.otp_last_sent_at < timedelta(seconds=60):
        return JsonResponse({'error': 'Espera un minuto antes de reenviar el código.'}, status=429)

    otp = f'{secrets.randbelow(1_000_000):06d}'
    defaults = {
        'name': name,
        'phone_prefix': phone_prefix,
        'phone_number': clean_phone,
        'otp_code': make_password(otp),
        'otp_expires_at': now + timedelta(minutes=10),
        'otp_attempts': 0,
        'otp_last_sent_at': now,
        'email_verified': False,
        'privacy_accepted_at': now,
        'privacy_policy_version': getattr(settings, 'PRIVACY_POLICY_VERSION', '2026-07-15'),
        'consent_source_ip': client_ip(request),
    }
    lead, _ = AILead.objects.update_or_create(email=email, defaults=defaults)

    safe_name = escape(name)
    html_message = (
        '<h2>Verifica tu correo electrónico</h2>'
        f'<p>Hola <strong>{safe_name}</strong>. Tu código de acceso a Fenix es:</p>'
        f'<p style="font-size:32px;font-weight:bold;letter-spacing:.2em">{otp}</p>'
        '<p>Caduca en 10 minutos. Si no lo solicitaste, ignora este mensaje.</p>'
    )
    try:
        send_mail(
            subject='Tu código de acceso - Fenix Assistant',
            message=f'Tu código de acceso es: {otp}. Caduca en 10 minutos.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
            html_message=html_message,
        )
    except Exception:
        logger.exception('No se pudo enviar el OTP del asistente')
        return JsonResponse({'error': 'No se pudo enviar el código. Inténtalo más tarde.'}, status=503)

    try:
        CRMLeadService.log_lead(
            channel=CRMLead.CHANNEL_WEB_ASSISTANT,
            full_name=name,
            email=email,
            phone=f'{phone_prefix}{clean_phone}',
            source='Fenix Assistant (OTP Request)',
            message='Solicitud de acceso al asistente',
        )
    except Exception:
        logger.exception('No se pudo sincronizar el lead del asistente con CRM')

    return JsonResponse({'success': True, 'message': 'Código enviado.', 'email': email, 'requires_otp': True})


@require_POST
def verify_otp(request):
    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    email = str(data.get('email', '')).strip().lower()
    otp = str(data.get('otp', '')).strip()

    if rate_limited(request, 'ai-verify-ip', 10, 15 * 60) or rate_limited(
        request, 'ai-verify-email', 5, 15 * 60, email
    ):
        return JsonResponse({'error': 'Demasiados intentos. Inténtalo más tarde.'}, status=429)

    lead = AILead.objects.filter(email=email).first()
    invalid = not lead or not lead.otp_code or not lead.otp_expires_at
    if invalid:
        return JsonResponse({'error': 'Código no válido o expirado.'}, status=400)
    if lead.otp_expires_at < timezone.now() or lead.otp_attempts >= 3:
        return JsonResponse({'error': 'Código no válido o expirado.'}, status=400)

    if not check_password(otp, lead.otp_code):
        lead.otp_attempts += 1
        lead.save(update_fields=['otp_attempts', 'updated_at'])
        return JsonResponse({'error': 'Código no válido o expirado.'}, status=400)

    lead.email_verified = True
    lead.otp_code = None
    lead.otp_expires_at = None
    lead.queries_used = 0
    lead.reset_at = timezone.now() + timedelta(days=1)
    lead.save(update_fields=['email_verified', 'otp_code', 'otp_expires_at', 'queries_used', 'reset_at', 'updated_at'])
    request.session.cycle_key()
    request.session['ai_verified_lead_id'] = lead.pk
    request.session.set_expiry(60 * 60)

    try:
        crm_lead = CRMLead.objects.filter(email=lead.email).first()
        if crm_lead:
            crm_lead.validation_status = CRMLead.VALIDATION_VALIDADO
            crm_lead.save(update_fields=['validation_status', 'updated_at'])
    except Exception:
        logger.exception('No se pudo actualizar la verificación del lead en CRM')
    return JsonResponse({'success': True, 'queries_remaining': 4})


@require_POST
def assistant_chat(request):
    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    if rate_limited(request, 'ai-chat-ip', 30, 10 * 60):
        return JsonResponse({'error': 'Demasiadas consultas. Inténtalo más tarde.'}, status=429)

    user_message = str(data.get('message', '')).strip()[:2000]
    history = data.get('history', [])
    if not user_message:
        return JsonResponse({'error': 'El mensaje está vacío.'}, status=400)
    if not isinstance(history, list):
        history = []
    history = history[-20:]
    is_auth = request.user.is_authenticated

    if is_auth:
        user = request.user
        email = user.email
        lead, _ = AILead.objects.get_or_create(
            email=email,
            defaults={
                'name': user.display_name if hasattr(user, 'display_name') else user.full_name,
                'phone_prefix': '+34',
                'phone_number': user.phone or getattr(user, 'telefono_reparto', '') or '',
                'email_verified': True,
            },
        )
    else:
        lead_id = request.session.get('ai_verified_lead_id')
        lead = AILead.objects.filter(pk=lead_id, email_verified=True).first()
        if not lead:
            return JsonResponse({'error': 'Debes verificar tu email primero.'}, status=401)
        email = lead.email

    if not is_auth:
        if not lead.reset_at or timezone.now() > lead.reset_at:
            lead.queries_used = 0
            lead.reset_at = timezone.now() + timedelta(days=1)
        if lead.queries_used >= 4:
            return JsonResponse({'response': 'Has alcanzado el límite diario de consultas.', 'is_quota_exceeded': True})

    try:
        ai_response = AIService.generate_response(
            user_message,
            history=history,
            is_authenticated=is_auth,
            user=request.user if is_auth else None,
        )
    except Exception:
        logger.exception('Error generando respuesta del asistente')
        return JsonResponse({'error': 'El asistente no está disponible temporalmente.'}, status=503)

    lead.queries_used += 1
    lead.save(update_fields=['queries_used', 'last_query_at', 'reset_at', 'updated_at'])
    try:
        crm_lead = CRMLead.objects.filter(email=email).first()
        if crm_lead:
            CRMLeadService.log_message(lead=crm_lead, channel=CRMLead.CHANNEL_WEB_ASSISTANT, sender='lead', message=user_message)
            CRMLeadService.log_message(lead=crm_lead, channel=CRMLead.CHANNEL_WEB_ASSISTANT, sender='ai', message=ai_response)
    except Exception:
        logger.exception('No se pudo registrar el chat en CRM')

    return JsonResponse({'response': ai_response, 'queries_remaining': 999 if is_auth else max(0, 4 - lead.queries_used)})
