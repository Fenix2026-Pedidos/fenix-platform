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
    leads_queryset = CRMLead.objects.all().select_related('assigned_to').order_by('-created_at')

    # 1. Aplicar Filtros Dinámicos
    query_search = request.GET.get('search', '').strip()
    query_channel = request.GET.get('channel', '').strip()
    query_status = request.GET.get('status', '').strip()
    query_validation = request.GET.get('validation', '').strip()
    query_priority = request.GET.get('priority', '').strip()
    query_zone = request.GET.get('zone', '').strip()
    query_agent = request.GET.get('agent', '').strip()
    
    # Filtros avanzados (fechas)
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

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
    if query_agent:
        leads_queryset = leads_queryset.filter(assigned_to_id=query_agent)
    
    if date_from:
        leads_queryset = leads_queryset.filter(created_at__date__gte=date_from)
    if date_to:
        leads_queryset = leads_queryset.filter(created_at__date__lte=date_to)

    # 2. Generar Métricas KPI de Ventas
    kpis = {
        'total': CRMLead.objects.count(),
        'nuevos': CRMLead.objects.filter(validation_status=CRMLead.VALIDATION_NUEVO).count(),
        'validados': CRMLead.objects.filter(validation_status=CRMLead.VALIDATION_VALIDADO).count(),
        'atendidos': CRMLead.objects.filter(validation_status=CRMLead.VALIDATION_ATENDIDO).count(),
        'convertidos': CRMLead.objects.filter(lead_status=CRMLead.STATUS_CONVERTIDO).count(),
    }

    # 3. Datos para filtros
    distinct_zones = CRMLead.objects.exclude(geographic_zone__isnull=True).exclude(geographic_zone='').values_list('geographic_zone', flat=True).distinct()
    staff_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('email')

    # 4. Paginación Pro
    per_page = int(request.GET.get('per_page', 20))
    paginator = Paginator(leads_queryset, per_page)
    page_number = request.GET.get('page', 1)
    leads_page = paginator.get_page(page_number)

    context = {
        'leads': leads_page,
        'kpis': kpis,
        'distinct_zones': sorted(list(distinct_zones)),
        'staff_users': staff_users,
        'channels': CRMLead.CHANNEL_CHOICES,
        'statuses': CRMLead.STATUS_CHOICES,
        'validations': CRMLead.VALIDATION_CHOICES,
        'priorities': CRMLead.PRIORITY_CHOICES,
        'per_page': per_page,
        'filters': {
            'search': query_search,
            'channel': query_channel,
            'status': query_status,
            'validation': query_validation,
            'priority': query_priority,
            'zone': query_zone,
            'agent': query_agent,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'crm/leads_list.html', context)


@crm_access_required
@require_POST
def delete_lead(request, lead_uuid):
    """Elimina un lead individual"""
    lead = get_object_or_404(CRMLead, uuid=lead_uuid)
    lead.delete()
    return JsonResponse({'success': True, 'message': 'Lead eliminado correctamente.'})


@crm_access_required
@require_POST
def bulk_delete_leads(request):
    """Elimina múltiples leads a la vez"""
    try:
        data = json.loads(request.body)
        lead_ids = data.get('ids', [])
        if not lead_ids:
            return JsonResponse({'success': False, 'error': 'No se seleccionaron leads.'}, status=400)
        
        CRMLead.objects.filter(uuid__in=lead_ids).delete()
        return JsonResponse({'success': True, 'message': f'{len(lead_ids)} leads eliminados correctamente.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@crm_access_required
def lead_detail(request, lead_uuid):
    """
    Vista detallada de la Ficha Comercial del Lead.
    Muestra la línea de tiempo, datos de contacto editables,
    asignación a comerciales y logging de interacciones.
    """
    from orders.models import Order
    from django.db.models import Sum, Avg, Max, Count
    
    lead = get_object_or_404(CRMLead, uuid=lead_uuid)
    timeline_messages = lead.messages.all().order_by('-timestamp') # Invertimos para que lo más reciente esté arriba
    
    # 1. Intentar vincular con un Usuario real para historial comercial
    linked_user = None
    if lead.email:
        linked_user = User.objects.filter(email=lead.email).first()
    if not linked_user and lead.phone:
        linked_user = User.objects.filter(phone=lead.phone).first()

    commercial_history = None
    if linked_user:
        orders = Order.objects.filter(customer=linked_user)
        stats = orders.aggregate(
            total_spent=Sum('total_amount'),
            avg_ticket=Avg('total_amount'),
            last_order_date=Max('created_at'),
            count=Count('id')
        )
        commercial_history = {
            'user': linked_user,
            'total_spent': stats['total_spent'] or 0,
            'avg_ticket': stats['avg_ticket'] or 0,
            'last_order_date': stats['last_order_date'],
            'order_count': stats['count'] or 0,
            'recent_orders': orders.order_by('-created_at')[:5]
        }
    
    # Obtener usuarios internos/vendedores para asignación
    staff_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('email')

    context = {
        'lead': lead,
        'timeline_messages': timeline_messages,
        'staff_users': staff_users,
        'statuses': CRMLead.STATUS_CHOICES,
        'validations': CRMLead.VALIDATION_CHOICES,
        'priorities': CRMLead.PRIORITY_CHOICES,
        'commercial_history': commercial_history,
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
