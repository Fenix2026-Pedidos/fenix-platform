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

        # 1. Generar OTP de 6 dígitos
        otp = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        # 2. Crear o actualizar lead
        lead, created = AILead.objects.update_or_create(
            email=email,
            defaults={
                'name': name,
                'phone_prefix': phone_prefix,
                'phone_number': phone_number,
                'otp_code': otp,
                'otp_expires_at': expires_at,
                'otp_attempts': 0,
                'email_verified': False
            }
        )

        # --- TAREAS EN SEGUNDO PLANO PARA NO BLOQUEAR EL FRONTEND ---
        def background_tasks(name, email, phone_prefix, phone_number, otp):
            # 3. Sincronizar con CRM (Google Sheets)
            try:
                CRMService.sync_lead({
                    "source": "Fenix Assistant (OTP Request)",
                    "name": name,
                    "email": email,
                    "phone_prefix": phone_prefix,
                    "phone_number": phone_number,
                    "message": "Solicitud de acceso al asistente"
                })
            except Exception as e:
                print(f"--- [AVISO CRM] Error al sincronizar: {e} ---")

            # 4. Enviar Email con el SMTP
            subject = 'Tu código de acceso - Fenix Assistant'
            message = f'''¡Hola {name}!
            
Tu código de verificación de 6 dígitos es: {otp}

Este código es válido durante 10 minutos.

Si no has solicitado este código, puedes ignorar este mensaje.

Un saludo,
El equipo de Fenix'''
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                print(f"--- [ÉXITO SMTP] Email enviado a {email} ---")
            except Exception as email_err:
                print(f"--- [AVISO SMTP] Error al enviar email: {email_err} ---")
                print(f"--- [OTP RESPALDO] Código para {email}: {otp} ---")

        # Iniciar el hilo en segundo plano
        threading.Thread(target=background_tasks, args=(name, email, phone_prefix, phone_number, otp)).start()
        
        # Como el email va en segundo plano, enviamos el fallback_otp siempre temporalmente 
        # para que puedas testear si Google sigue bloqueando el SMTP sin quedarte atascado.
        return JsonResponse({
            'success': True, 
            'message': 'OTP procesando en segundo plano.',
            'email': email,
            'fallback_otp': otp  # Temporal para el entorno de desarrollo
        })

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
            
            # Sincronizar confirmación en CRM
            CRMService.sync_lead({
                "source": "Fenix Assistant (Verified)",
                "name": lead.name,
                "email": lead.email,
                "phone_prefix": lead.phone_prefix,
                "phone_number": lead.phone_number,
                "message": "Email verificado correctamente"
            })

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
        lead_info = data.get('lead')
        history = data.get('history', [])
        
        if not lead_info or not lead_info.get('email'):
            return JsonResponse({'error': 'Acceso denegado.'}, status=403)

        email = lead_info.get('email')
        lead = AILead.objects.filter(email=email).first()

        if not lead or not lead.email_verified:
            return JsonResponse({'error': 'Debes verificar tu email primero.'}, status=401)

        # Control de cuota (24h)
        if lead.reset_at and timezone.now() > lead.reset_at:
            lead.queries_used = 0
            lead.reset_at = timezone.now() + timedelta(days=1)
            lead.save()

        if lead.queries_used >= 4:
            return JsonResponse({
                'response': 'Has alcanzado el límite de consultoría gratuita. Agenda una cita.',
                'is_quota_exceeded': True
            })

        # Generar respuesta
        ai_response = AIService.generate_response(user_message, history=history)
        
        lead.queries_used += 1
        lead.save()
        
        return JsonResponse({
            'response': ai_response,
            'queries_remaining': max(0, 4 - lead.queries_used)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
