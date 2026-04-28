import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .services import AIService

@csrf_exempt
@require_POST
def assistant_chat(request):
    """
    Endpoint para interactuar con el asistente inteligente siguiendo el Framework Synerg-IA.
    Incluye validación de leads y límite de cuota (5 mensajes).
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        lead = data.get('lead')
        history = data.get('history', [])
        
        # 1. VALIDACIÓN: Prohibido hablar sin lead (Synerg-IA Framework)
        if not lead or not lead.get('email'):
            return JsonResponse({
                'error': 'Acceso denegado. Por favor, completa el formulario para comenzar.'
            }, status=403)

        # 2. CONTROL DE CUOTA: Máximo 5 consultas por sesión/lead
        email = lead.get('email')
        quota_key = f'ai_quota_{email}'
        current_quota = request.session.get(quota_key, 0)
        
        if current_quota >= 5:
            return JsonResponse({
                'response': 'Has alcanzado el límite de consultoría gratuita por hoy. Para profundizar en una solución personalizada, te recomendamos contactar con nuestro equipo comercial.',
                'is_quota_exceeded': True
            })

        if not user_message:
            return JsonResponse({'error': 'El mensaje no puede estar vacío.'}, status=400)

        # 3. Recuperar contexto relevante de la base de conocimiento (RAG)
        context_fragments = AIService.search_knowledge(user_message, limit=3)
        
        # 4. Generar respuesta usando Gemini (con Gobernanza)
        # Aquí podrías pasar la historia si la guardas en sesión
        ai_response = AIService.generate_response(user_message, context_fragments)
        
        # Incrementar cuota
        request.session[quota_key] = current_quota + 1
        
        return JsonResponse({
            'response': ai_response,
            'has_context': context_fragments.exists()
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
