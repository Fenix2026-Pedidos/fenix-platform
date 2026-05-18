import threading
import json
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from core.crm_services import CRMService
from crm.services import CRMLeadService
from crm.models import CRMLead
from .models import AILead
from .services import AIService

@csrf_exempt
@require_POST
def capture_lead(request):
    """
    Captura los datos iniciales del lead y envía el código OTP.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        phone_prefix = data.get('phone_prefix', '+34')
        phone_number = data.get('phone_number')
        privacy_accepted = data.get('privacy_accepted')

        if not all([name, email, phone_number, privacy_accepted]):
            return JsonResponse({'error': 'Faltan campos obligatorios.'}, status=400)

        # --- VALIDACIÓN DEL TELÉFONO EN EL SERVIDOR ---
        import re
        clean_phone = re.sub(r'[\s\-()]+', '', phone_number)
        if phone_prefix == "+34":
            if not re.match(r'^[6789]\d{8}$', clean_phone):
                return JsonResponse({'error': 'El teléfono de España debe tener 9 dígitos y empezar por 6, 7, 8 o 9.'}, status=400)
        else:
            if not re.match(r'^\d{7,15}$', clean_phone):
                return JsonResponse({'error': 'El número de teléfono debe tener entre 7 y 15 dígitos.'}, status=400)

        # 1. Generar OTP de 6 dígitos
        otp = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        # 2. Crear o actualizar lead
        lead, created = AILead.objects.update_or_create(
            email=email,
            defaults={
                'name': name,
                'phone_prefix': phone_prefix,
                'phone_number': clean_phone,
                'otp_code': otp,
                'otp_expires_at': expires_at,
                'otp_attempts': 0,
                'email_verified': False  # Requerimos verificación
            }
        )

        # --- TAREAS EN SEGUNDO PLANO PARA NO BLOQUEAR EL FRONTEND ---
        def background_tasks(name, email, phone_prefix, phone_number, otp):
            # 3. Sincronizar con CRM Unificado
            try:
                CRMLeadService.log_lead(
                    channel=CRMLead.CHANNEL_WEB_ASSISTANT,
                    full_name=name,
                    email=email,
                    phone=f"{phone_prefix}{phone_number}",
                    source="Fenix Assistant (OTP Request)",
                    message="Solicitud de acceso al asistente"
                )
            except Exception as e:
                print(f"--- [AVISO CRM] Error al registrar lead CRM: {e} ---")

            # 4. Enviar Email Premium HTML
            subject = 'Tu código de acceso - Fenix Assistant'
            
            html_message = f"""
            <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 0; -webkit-font-smoothing: antialiased;">
                <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(15,23,42,0.05); border: 1px solid #f1f5f9;">
                    <tr>
                        <td style="background-color: #0b4629; padding: 40px 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.03em; font-family: 'Outfit', sans-serif;">Plataforma Fénix</h1>
                            <p style="color: #a7f3d0; margin: 8px 0 0 0; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em;">Smart Assistant</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 35px; text-align: center;">
                            <h2 style="color: #0f172a; margin-top: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.02em;">Verifica tu correo electrónico</h2>
                            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 16px 0 32px 0;">Hola <strong>{name}</strong>,<br>Usa el siguiente código de verificación de 6 dígitos para acceder al asistente virtual comercial de Fénix.</p>
                            
                            <div style="background-color: #f8fafc; border: 2px dashed #e2e8f0; border-radius: 16px; padding: 24px 40px; display: inline-block; margin-bottom: 32px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.01);">
                                <span style="font-size: 36px; font-weight: 800; letter-spacing: 0.2em; color: #0b4629; font-family: 'Courier New', Courier, monospace; display: block; margin-left: 0.1em;">{otp}</span>
                            </div>
                            
                            <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin: 0 0 12px 0;">Este código de un solo uso es válido durante <strong>10 minutos</strong>.</p>
                            <p style="color: #94a3b8; font-size: 12px; line-height: 1.5; margin: 0;">Si no has solicitado este código, puedes ignorar este mensaje con total seguridad.</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #fafafa; padding: 24px 30px; text-align: center; border-top: 1px solid #f1f5f9;">
                            <p style="color: #94a3b8; font-size: 11px; margin: 0; font-weight: 500;">© 2026 Plataforma Fénix. Todos los derechos reservados.</p>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            try:
                send_mail(
                    subject=subject,
                    message=f"Tu código de verificación de 6 dígitos es: {otp}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                    html_message=html_message
                )
                print(f"--- [ÉXITO SMTP] Email HTML enviado a {email} ---")
            except Exception as email_err:
                print(f"--- [AVISO SMTP] Error al enviar email: {email_err} ---")
                print(f"--- [OTP RESPALDO] Código para {email}: {otp} ---")

        # Iniciar el hilo en segundo plano
        threading.Thread(target=background_tasks, args=(name, email, phone_prefix, clean_phone, otp)).start()
        
        response_data = {
            'success': True, 
            'message': 'Código enviado. Por favor, verifica tu email.',
            'email': email,
            'requires_otp': True
        }
        if settings.DEBUG:
            response_data['fallback_otp'] = otp

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def verify_otp(request):
    """
    Verifica el código OTP enviado al email del lead.
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        otp = data.get('otp')

        lead = AILead.objects.filter(email=email).first()
        if not lead:
            return JsonResponse({'error': 'Lead no encontrado.'}, status=404)

        if lead.otp_expires_at < timezone.now():
            return JsonResponse({'error': 'El código ha expirado.'}, status=400)

        if lead.otp_attempts >= 3:
            return JsonResponse({'error': 'Límite de intentos superado.'}, status=403)

        if lead.otp_code == otp:
            lead.email_verified = True
            lead.otp_code = None
            lead.queries_used = 0
            lead.reset_at = timezone.now() + timedelta(days=1)
            lead.save()
            
            # Sincronizar confirmación en CRM Unificado
            try:
                # 1. Buscar lead primero por email
                crm_lead = CRMLead.objects.filter(email=lead.email).first()
                # 2. Si no se encuentra por email, buscar por teléfono para unificar
                if not crm_lead:
                    crm_lead = CRMLead.objects.filter(phone=f"{lead.phone_prefix}{lead.phone_number}").first()
                
                if crm_lead:
                    # Registrar mensaje de validación en el CRM
                    CRMLeadService.log_message(
                        lead=crm_lead,
                        channel=CRMLead.CHANNEL_WEB_ASSISTANT,
                        sender='system',
                        message=f"Email verificado correctamente mediante OTP ({lead.email})"
                    )
                    # Sincronizar el email validado con el CRM lead
                    if not crm_lead.email or crm_lead.email != lead.email:
                        crm_lead.email = lead.email

                    crm_lead.validation_status = CRMLead.VALIDATION_VALIDADO
                    crm_lead.save(update_fields=['validation_status', 'email', 'updated_at'])
            except Exception as e:
                print(f"--- [AVISO CRM] Error actualizando verificación: {e} ---")

            return JsonResponse({'success': True, 'queries_remaining': 4})
        else:
            lead.otp_attempts += 1
            lead.save()
            return JsonResponse({'error': 'Código incorrecto.'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def assistant_chat(request):
    """
    Endpoint para interactuar con el asistente inteligente.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        history = data.get('history', [])
        is_auth = request.user.is_authenticated
        
        if is_auth:
            user = request.user
            email = user.email
            
            # Obtener o crear AILead para mantener compatibilidad con contadores u otros procesos
            lead, created = AILead.objects.get_or_create(
                email=email,
                defaults={
                    'name': user.display_name if hasattr(user, 'display_name') else user.full_name,
                    'phone_prefix': '+34',
                    'phone_number': user.phone or getattr(user, 'telefono_reparto', '') or '',
                    'email_verified': True
                }
            )
            if not lead.email_verified:
                lead.email_verified = True
                lead.save()
        else:
            # Flujo Anónimo: requiere lead registrado y email verificado
            email = None
            lead_info = data.get('lead')
            if isinstance(lead_info, dict):
                email = lead_info.get('email')
            elif isinstance(lead_info, str):
                email = lead_info
                
            if not email:
                email = data.get('lead_id') or data.get('email')
                
            if not email:
                return JsonResponse({'error': 'Acceso denegado. Se requiere el email del lead.'}, status=403)
                
            lead = AILead.objects.filter(email=email).first()
            if not lead or not lead.email_verified:
                return JsonResponse({'error': 'Debes verificar tu email primero.'}, status=401)

        # Control de cuota (Solo aplica a leads anónimos, usuarios registrados tienen consultas ilimitadas)
        if not is_auth:
            # Corrección crítica: Si reset_at es None, lo inicializamos para permitir el reinicio de cuota dentro de 24h
            if not lead.reset_at:
                lead.reset_at = timezone.now() + timedelta(days=1)
                lead.save()
            elif timezone.now() > lead.reset_at:
                lead.queries_used = 0
                lead.reset_at = timezone.now() + timedelta(days=1)
                lead.save()

            if lead.queries_used >= 4:
                return JsonResponse({
                    'response': 'Has alcanzado el límite diario de consultoría gratuita. Estaremos encantados de atenderte en una sesión de asesoramiento comercial personalizado.\n\n[Agendar Cita](/contacto/) [Hablar por WhatsApp](https://wa.me/34624149250)',
                    'is_quota_exceeded': True
                })

        # Generar respuesta incluyendo objeto de usuario autenticado para RAG personalizado
        ai_response = AIService.generate_response(
            user_message, 
            history=history, 
            is_authenticated=is_auth,
            user=request.user if is_auth else None
        )
        
        # Incrementar contador (solo para control analítico, o cuota si es anónimo)
        lead.queries_used += 1
        lead.save()
        
        # Registrar conversación en el historial del CRM
        try:
            # Buscar el lead en el CRM por el email asociado a la sesión de chat
            crm_lead = CRMLead.objects.filter(email=email).first()
            if not crm_lead and not is_auth and lead:
                crm_lead = CRMLead.objects.filter(phone=f"{lead.phone_prefix}{lead.phone_number}").first()
            
            if crm_lead:
                # 1. Registrar mensaje del lead
                CRMLeadService.log_message(
                    lead=crm_lead,
                    channel=CRMLead.CHANNEL_WEB_ASSISTANT,
                    sender='lead',
                    message=user_message
                )
                # 2. Registrar respuesta de la IA
                CRMLeadService.log_message(
                    lead=crm_lead,
                    channel=CRMLead.CHANNEL_WEB_ASSISTANT,
                    sender='ai',
                    message=ai_response
                )
        except Exception as chat_err:
            print(f"--- [AVISO CRM] Error registrando chat en el CRM: {chat_err} ---")
        
        return JsonResponse({
            'response': ai_response,
            'queries_remaining': 999 if is_auth else max(0, 4 - lead.queries_used)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
