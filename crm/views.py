import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from accounts.utils import is_manager_or_admin

def crm_access_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not is_manager_or_admin(request.user):
            raise PermissionDenied("No tienes permisos para acceder al CRM de Fenix.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone

from .models import CRMLead, CRMLeadMessage
from .services import CRMLeadService

User = get_user_model()

@crm_access_required
def leads_list(request):
    """
    Vista del Dashboard del CRM. Muestra listado de leads con filtros premium,
    KPIs comerciales y paginación rápida.
    """
    leads_queryset = CRMLead.objects.all().select_related('assigned_to')

    # 1. Aplicar Filtros Dinámicos
    query_search = request.GET.get('search', '').strip()
    query_channel = request.GET.get('channel', '').strip()
    query_status = request.GET.get('status', '').strip()
    query_validation = request.GET.get('validation', '').strip()
    query_priority = request.GET.get('priority', '').strip()
    query_zone = request.GET.get('zone', '').strip()

    if query_search:
        leads_queryset = leads_queryset.filter(
            Q(full_name__icontains=query_search) |
            Q(phone__icontains=query_search) |
            Q(email__icontains=query_search) |
            Q(company_name__icontains=query_search) |
            Q(notes__icontains=query_search)
        )

    if query_channel:
        leads_queryset = leads_queryset.filter(channel=query_channel)

    if query_status:
        leads_queryset = leads_queryset.filter(lead_status=query_status)

    if query_validation:
        leads_queryset = leads_queryset.filter(validation_status=query_validation)

    if query_priority:
        leads_queryset = leads_queryset.filter(priority=query_priority)

    if query_zone:
        leads_queryset = leads_queryset.filter(geographic_zone__iexact=query_zone)

    # 2. Generar Métricas KPI de Ventas (Basadas en el queryset total actual)
    kpis = {
        'total': CRMLead.objects.count(),
        'nuevos': CRMLead.objects.filter(validation_status=CRMLead.VALIDATION_NUEVO).count(),
        'validados': CRMLead.objects.filter(validation_status=CRMLead.VALIDATION_VALIDADO).count(),
        'atendidos': CRMLead.objects.filter(validation_status=CRMLead.VALIDATION_ATENDIDO).count(),
        'convertidos': CRMLead.objects.filter(lead_status=CRMLead.STATUS_CONVERTIDO).count(),
    }

    # 3. Obtener listado de Zonas Geográficas únicas para poblar el filtro dropdown
    distinct_zones = CRMLead.objects.exclude(geographic_zone__isnull=True).exclude(geographic_zone='').values_list('geographic_zone', flat=True).distinct()

    # 4. Paginación
    paginator = Paginator(leads_queryset, 15)  # 15 leads por página
    page_number = request.GET.get('page', 1)
    leads_page = paginator.get_page(page_number)

    context = {
        'leads': leads_page,
        'kpis': kpis,
        'distinct_zones': sorted(list(distinct_zones)),
        'channels': CRMLead.CHANNEL_CHOICES,
        'statuses': CRMLead.STATUS_CHOICES,
        'validations': CRMLead.VALIDATION_CHOICES,
        'priorities': CRMLead.PRIORITY_CHOICES,
        'filters': {
            'search': query_search,
            'channel': query_channel,
            'status': query_status,
            'validation': query_validation,
            'priority': query_priority,
            'zone': query_zone,
        }
    }
    return render(request, 'crm/leads_list.html', context)


@crm_access_required
def lead_detail(request, lead_uuid):
    """
    Vista detallada de la Ficha Comercial del Lead.
    Muestra la línea de tiempo, datos de contacto editables,
    asignación a comerciales y logging de interacciones.
    """
    lead = get_object_or_404(CRMLead, uuid=lead_uuid)
    messages = lead.messages.all().order_index = ['timestamp'] # Orden cronológico
    messages = lead.messages.all().order_by('timestamp')
    
    # Obtener usuarios internos/vendedores para asignación
    staff_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('email')

    context = {
        'lead': lead,
        'messages': messages,
        'staff_users': staff_users,
        'statuses': CRMLead.STATUS_CHOICES,
        'validations': CRMLead.VALIDATION_CHOICES,
        'priorities': CRMLead.PRIORITY_CHOICES,
    }
    return render(request, 'crm/lead_detail.html', context)


@crm_access_required
@require_POST
def update_lead(request, lead_uuid):
    """
    Endpoint AJAX para actualizar campos individuales o agrupados de un Lead.
    """
    lead = get_object_or_404(CRMLead, uuid=lead_uuid)
    
    try:
        # Soportar POST convencional o JSON payload
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        # Campos editables comerciales
        full_name = data.get('full_name')
        company_name = data.get('company_name')
        phone = data.get('phone')
        email = data.get('email')
        lead_status = data.get('lead_status')
        validation_status = data.get('validation_status')
        priority = data.get('priority')
        geographic_zone = data.get('geographic_zone')
        notes = data.get('notes')
        estimated_value = data.get('estimated_value')
        assigned_to_id = data.get('assigned_to')

        # Registrar cambios para el historial
        changes = []

        if full_name and full_name != lead.full_name:
            changes.append(f"Nombre: '{lead.full_name}' -> '{full_name}'")
            lead.full_name = full_name

        if company_name is not None and company_name != lead.company_name:
            changes.append(f"Empresa: '{lead.company_name}' -> '{company_name}'")
            lead.company_name = company_name

        if phone is not None and phone != lead.phone:
            changes.append(f"Teléfono: '{lead.phone}' -> '{phone}'")
            lead.phone = phone

        if email is not None and email != lead.email:
            changes.append(f"Email: '{lead.email}' -> '{email}'")
            lead.email = email

        if geographic_zone is not None and geographic_zone != lead.geographic_zone:
            changes.append(f"Zona Geográfica: '{lead.geographic_zone}' -> '{geographic_zone}'")
            lead.geographic_zone = geographic_zone

        if lead_status and lead_status != lead.lead_status:
            old_status_disp = lead.get_lead_status_display()
            lead.lead_status = lead_status
            new_status_disp = lead.get_lead_status_display()
            changes.append(f"Estado Comercial: '{old_status_disp}' -> '{new_status_disp}'")

        if validation_status and validation_status != lead.validation_status:
            old_val_disp = lead.get_validation_status_display()
            lead.validation_status = validation_status
            new_val_disp = lead.get_validation_status_display()
            changes.append(f"Estado de Validación: '{old_val_disp}' -> '{new_val_disp}'")

        if priority and priority != lead.priority:
            old_prio_disp = lead.get_priority_display()
            lead.priority = priority
            new_prio_disp = lead.get_priority_display()
            changes.append(f"Prioridad: '{old_prio_disp}' -> '{new_prio_disp}'")

        if notes is not None and notes != lead.notes:
            lead.notes = notes
            # Notas no se detallan en cambios para evitar logs masivos, pero se guarda el cambio
            changes.append("Notas comerciales actualizadas")

        if estimated_value is not None:
            try:
                val = float(estimated_value) if estimated_value != '' else None
                if val != lead.estimated_value:
                    changes.append(f"Valor Estimado: {lead.estimated_value or 0}€ -> {val or 0}€")
                    lead.estimated_value = val
            except ValueError:
                pass

        if assigned_to_id is not None:
            if assigned_to_id == '':
                if lead.assigned_to:
                    changes.append(f"Vendedor: {lead.assigned_to.full_name} -> Sin asignar")
                    lead.assigned_to = None
            else:
                user = get_object_or_404(User, id=assigned_to_id)
                if user != lead.assigned_to:
                    old_name = lead.assigned_to.full_name if lead.assigned_to else "Sin asignar"
                    lead.assigned_to = user
                    changes.append(f"Vendedor: {old_name} -> {user.full_name or user.email}")

        # Guardar si hay cambios
        if changes:
            lead.save()
            # Log de sistema en la cronología
            CRMLeadService.log_message(
                lead=lead,
                channel=lead.channel,
                sender=CRMLeadMessage.SENDER_SYSTEM,
                message=f"Campos actualizados por {request.user.full_name or request.user.email}:\n" + "\n".join([f"- {c}" for c in changes])
            )
            return JsonResponse({'success': True, 'message': 'Lead actualizado correctamente.'})
        
        return JsonResponse({'success': True, 'message': 'No se detectaron cambios.'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@crm_access_required
@require_POST
def add_lead_message(request, lead_uuid):
    """
    Endpoint AJAX para registrar una nota de seguimiento o mensaje manual en el timeline.
    """
    lead = get_object_or_404(CRMLead, uuid=lead_uuid)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        message = data.get('message', '').strip()
        is_note = data.get('is_note', False)  # Si es True, se marca como nota de sistema; si no, mensaje de agente

        if not message:
            return JsonResponse({'success': False, 'error': 'El mensaje no puede estar vacío.'}, status=400)

        sender = CRMLeadMessage.SENDER_SYSTEM if is_note else CRMLeadMessage.SENDER_AGENT
        
        # Guardar en la línea de tiempo
        CRMLeadService.log_message(
            lead=lead,
            channel=lead.channel,
            sender=sender,
            message=message,
            metadata={
                'author': request.user.full_name or request.user.email,
                'author_id': request.user.id
            }
        )

        return JsonResponse({'success': True, 'message': 'Interacción guardada en la línea de tiempo.'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
