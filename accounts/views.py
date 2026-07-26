from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from core.rate_limit import rate_limited
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import User, EmailVerificationToken
from .forms import LoginForm, RegisterForm
from .utils import send_verification_email, send_approval_notification, is_manager_or_admin
from .permissions import (
    can_manage_users,
    can_edit_target,
    can_assign_role,
    can_delete_target,
    get_visible_users_queryset,
    get_role_choices_for_user,
    admin_required,
)


def _wants_json(request):
    """Detecta las acciones AJAX del panel sin romper los formularios legacy."""
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Accept', '')
    )


def _management_counts(editor):
    registered = User.objects.filter(
        status__in=[
            User.STATUS_ACTIVE,
            User.STATUS_DISABLED,
            User.STATUS_REJECTED,
        ]
    )
    registered = get_visible_users_queryset(editor, registered)
    pending = User.objects.filter(status=User.STATUS_PENDING)
    pending = get_visible_users_queryset(editor, pending)
    return {
        'registered': registered.count(),
        'pending': pending.count(),
    }


def _json_error(message, *, status=400):
    return JsonResponse({'ok': False, 'message': str(message)}, status=status)


@login_required
def dashboard_view(request):
    """Vista principal del Dashboard/Inicio de Fénix"""
    from orders.models import Order
    from notifications.models import Notification
    from datetime import datetime
    
    user = request.user
    
    # Calcular límites del mes en curso
    now = timezone.now()
    month_start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=now.tzinfo)
    
    # Mis Pedidos (Order usa 'customer' no 'user')
    # "Pedidos en mes en curso" = pedidos entregados con delivered_at dentro del mes en curso
    delivered_this_month_count = Order.objects.filter(
        customer=user,
        status=Order.STATUS_DELIVERED,
        delivered_at__gte=month_start,
        delivered_at__lte=now
    ).count()
    
    # "Pendientes" = pedidos no entregados (cualquier estado excepto DELIVERED)
    pending_orders = Order.objects.filter(customer=user).exclude(status=Order.STATUS_DELIVERED).count()
    
    last_order = Order.objects.filter(customer=user).order_by('-created_at').first()
    
    # Acciones Pendientes (notificaciones sin leer)
    try:
        pending_actions = Notification.objects.filter(user=user, read=False).count()
    except Exception:
        pending_actions = 0
    
    # Actividad Reciente
    recent_order = Order.objects.filter(customer=user, status__in=['confirmed', 'processing', 'shipped']).order_by('-updated_at').first()
    
    # Promoción activa (feature toggle - puedes controlarlo desde settings o base de datos)
    active_promotion = {
        'enabled': True,  # Cambiar a False para ocultar
        'title': _('Oferta especial'),
        'description': _('-10% en pedidos esta semana'),
        'icon': '🎁',
        'url': 'catalog:product_list',
    }
    
    context = {
        'delivered_this_month_count': delivered_this_month_count,
        'pending_orders_count': pending_orders,
        'last_order': last_order,
        'pending_actions_count': pending_actions,
        'recent_order': recent_order,
        'active_promotion': active_promotion if active_promotion['enabled'] else None,
    }
    
    return render(request, 'dashboard/index.html', context)


def login_view(request):
    """Vista de inicio de sesión con verificación de email"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        post_data = request.POST.copy()
        if not post_data.get('username') and post_data.get('email'):
            post_data['username'] = post_data['email']
        identity = post_data.get('username') or ''
        if rate_limited(request, 'login-ip', 15, 15 * 60) or rate_limited(request, 'login-identity', 10, 15 * 60, identity):
            messages.error(request, _('Demasiados intentos. Inténtalo de nuevo más tarde.'))
            return render(request, 'accounts/login.html', {'form': LoginForm(request, data=post_data)}, status=429)
        form = LoginForm(request, data=post_data)
        if form.is_valid():
            user = form.get_user()
            
            # GATE DE SEGURIDAD: Dos checks obligatorios
            # 1. Email debe estar verificado
            if not user.email_verified:
                request.session['unverified_user_email'] = user.email
                messages.error(request, _('Debes verificar tu email antes de iniciar sesión.'))
                return redirect('accounts:email_verification')
            
            # 2. Cuenta debe estar aprobada (status = ACTIVE)
            if user.status != User.STATUS_ACTIVE:
                request.session['pending_user_email'] = user.email
                
                if user.status == User.STATUS_REJECTED:
                    messages.error(request, _('Tu cuenta ha sido rechazada. Contacta con soporte.'))
                elif user.status == User.STATUS_DISABLED:
                    messages.error(request, _('Tu cuenta ha sido deshabilitada. Contacta con soporte.'))
                else:  # STATUS_PENDING
                    messages.warning(request, _('Tu cuenta está pendiente de aprobación por un administrador.'))
                
                return redirect('accounts:pending_approval')
            
            # Si pasa ambos checks, permitir login
            if not user.is_active:
                messages.error(request, _('Tu cuenta está desactivada por el sistema.'))
            else:
                # Comprobar si tiene 2FA habilitado
                security = getattr(user, 'security', None)
                if security and security.two_factor_enabled:
                    request.session['pre_2fa_user_id'] = user.id
                    next_url = request.GET.get('next')
                    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                        request.session['next_url'] = next_url
                    return redirect('accounts:verify_2fa_login')
                else:
                    login(request, user)
                    next_url = request.GET.get('next')
                    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                        return redirect(next_url)
                    return redirect('accounts:dashboard')
    else:
        form = LoginForm(request)
    
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """Vista de registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.role = User.ROLE_USER  # SIEMPRE role='user' en registro público
            user.pending_approval = True  # Requiere aprobación del manager
            user.status = User.STATUS_PENDING  # Estado pendiente
            user.email_verified = False
            user.is_active = True  # Activo pero pendiente de aprobación
            user.save()
            
            # Sincronizar con CRM (Google Sheets) de Fenix
            try:
                from core.crm_services import CRMService
                CRMService.sync_lead({
                    "source": "Registro Plataforma Fenix",
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "phone_prefix": user.phone_prefix or "+34",
                    "phone_number": user.phone_number or "",
                    "company": user.vat_number or "-",
                    "message": f"Nuevo registro: {user.job_title}"
                })
            except Exception as e:
                print(f"Error syncing with CRM: {e}")
            
            # Enviar email de verificación con token
            try:
                verification_url = request.build_absolute_uri(reverse('accounts:verify_email'))
                send_verification_email(user, verification_url)
            except Exception as e:
                print(f"Error sending verification email: {e}")
                pass  # No fallar el registro si el email falla
            
            # Enviar notificación al administrador
            try:
                from .utils import send_new_user_admin_notification
                send_new_user_admin_notification(user, request)
            except Exception as e:
                print(f"Error sending admin notification: {e}")
                pass  # No fallar el registro si el email falla
            
            messages.success(
                request,
                _('Registro exitoso. Por favor verifica tu email para continuar.')
            )
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def email_verification_view(request):
    """Vista informativa de verificación de email pendiente"""
    email = request.session.get('unverified_user_email', '')
    return render(request, 'accounts/email_verification.html', {'email': email})


def pending_approval_view(request):
    """Vista informativa de aprobación pendiente"""
    context = {
        'verified_user_email': request.session.get('verified_user_email', ''),
        'pending_user_email': request.session.get('pending_user_email', ''),
    }
    return render(request, 'accounts/pending_approval.html', context)


def verify_email(request):
    """Vista para verificar el email usando el token"""
    token_str = request.GET.get('token')
    
    if not token_str:
        messages.error(request, _('Token de verificación no válido.'))
        return redirect('accounts:login')
    
    try:
        token = EmailVerificationToken.objects.get(token=token_str)
        
        if not token.is_valid():
            messages.error(request, _('Este enlace de verificación ha expirado o ya fue usado.'))
            return redirect('accounts:login')
        
        # Marcar email como verificado
        user = token.user
        user.email_verified = True
        user.save()
        
        # Marcar token como usado
        token.is_used = True
        token.save()
        
        # NO iniciar sesión - redirigir a página de "pendiente de aprobación"
        request.session['verified_user_email'] = user.email
        request.session['pending_user_email'] = user.email  # Backup para compatibilidad
        request.session.save()  # Asegurar que la sesión se guarda
        messages.success(request, _('¡Email verificado exitosamente! Tu cuenta está pendiente de aprobación por un administrador.'))
        return redirect('accounts:pending_approval')
        
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, _('Token de verificación no válido.'))
        return redirect('accounts:login')


@require_POST
def resend_confirmation(request):
    """Reenviar email de confirmación"""
    email = request.POST.get('email')
    
    if not email:
        return JsonResponse({'success': False, 'error': _('Email requerido.')}, status=400)
    
    try:
        user = User.objects.get(email=email)
        
        if user.email_verified:
            return JsonResponse({'success': False, 'error': _('El email ya está verificado.')}, status=400)
        
        # Verificar si ya hay un token válido reciente (últimos 5 minutos)
        from django.utils import timezone
        from datetime import timedelta
        recent_token = EmailVerificationToken.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(minutes=5),
            is_used=False
        ).first()
        
        if recent_token:
            return JsonResponse({
                'success': False, 
                'error': _('Ya se envió un email recientemente. Por favor espera unos minutos.')
            }, status=429)
        
        # Enviar nuevo email de verificación
        verification_url = request.build_absolute_uri(reverse('accounts:verify_email'))
        send_verification_email(user, verification_url)
        
        return JsonResponse({
            'success': True, 
            'message': _('Email de confirmación enviado.')
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Usuario no encontrado.')}, status=404)


def logout_view(request):
    """Vista personalizada de logout que maneja tanto GET como POST"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, _('Has cerrado sesión correctamente.'))
    return redirect('/')


@login_required
def profile_view(request):
    """Vista del perfil del usuario"""
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
@admin_required
@login_required
@admin_required
def user_approval_list(request):
    """
    Vista MEJORADA: Dashboard de gestión de usuarios con paginación moderna.
    
    Features:
    - PAGINACIÓN: query params ?per_page=10&page=2
    - FILTROS: status, search (preservados en paginación)
    - RBAC: SUPER_ADMIN ve todos, ADMIN ve todos menos super_admin
    - TABS: Usuarios registrados | Nuevos usuarios pendientes (aprobación)
    """
    from django.core.paginator import Paginator
    
    # Obtener parámetros
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    current_page = request.GET.get('page', '1')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    active_tab = request.GET.get('tab', 'registered')
    
    # ========== TAB 1: USUARIOS REGISTRADOS ==========
    base_registered = User.objects.filter(
        status__in=[User.STATUS_ACTIVE, User.STATUS_DISABLED, User.STATUS_REJECTED]
    )
    
    # Filtrar según RBAC
    registered_users = get_visible_users_queryset(request.user, base_registered)
    registered_users = registered_users.order_by('-date_joined')
    
    # Aplicar filtros
    if status_filter and status_filter in [User.STATUS_ACTIVE, User.STATUS_DISABLED, User.STATUS_REJECTED]:
        registered_users = registered_users.filter(status=status_filter)
    
    if search_query:
        registered_users = registered_users.filter(
            Q(email__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(company__icontains=search_query)
        )
    
    # PAGINACIÓN TAB 1
    paginator_registered = Paginator(registered_users, per_page)
    try:
        page_registered = paginator_registered.page(current_page)
    except Exception:
        page_registered = paginator_registered.page(1)
    
    # ========== TAB 2: USUARIOS PENDIENTES ==========
    pending_new_users = User.objects.filter(status=User.STATUS_PENDING)
    pending_new_users = get_visible_users_queryset(
        request.user,
        pending_new_users,
    ).order_by('-date_joined')
    
    # PAGINACIÓN TAB 2
    paginator_pending = Paginator(pending_new_users, per_page)
    try:
        page_pending = paginator_pending.page(current_page)
    except Exception:
        page_pending = paginator_pending.page(1)
    
    # Construir query string para preservar filtros
    query_params = {
        'per_page': per_page,
        'status': status_filter,
        'search': search_query,
        'tab': active_tab,
    }
    query_string = '&'.join(f'{k}={v}' for k, v in query_params.items() if v)
    
    # Obtener opciones de roles
    available_role_choices = get_role_choices_for_user(request.user)
    
    context = {
        # TAB 1: Usuarios registrados (paginado)
        'page_registered': page_registered,
        'paginator_registered': paginator_registered,
        
        # TAB 2: Usuarios pendientes (paginado)
        'page_pending': page_pending,
        'paginator_pending': paginator_pending,
        
        # Parámetros
        'per_page': per_page,
        'per_page_choices': [10, 20, 50, 100],
        'status_filter': status_filter,
        'search_query': search_query,
        'query_string': query_string,
        'active_tab': active_tab,
        
        # Opciones
        'status_choices': [
            (User.STATUS_ACTIVE, _('Activo')),
            (User.STATUS_DISABLED, _('Deshabilitado')),
            (User.STATUS_REJECTED, _('Rechazado')),
        ],
        'available_role_choices': available_role_choices,
        'user_is_super_admin': request.user.is_super_admin(),
    }
    return render(request, 'accounts/user_management_modern.html', context)


@login_required
@admin_required
@require_POST
def user_update_view(request, user_id):
    """
    Actualiza información de un usuario (CRUD Update).
    
    RBAC:
    - SUPER_ADMIN puede editar a cualquiera
    - ADMIN puede editar user y admin, pero NO super_admin
    - ADMIN no puede asignar role='super_admin'
    """
    user_to_update = get_object_or_404(User, pk=user_id)
    
    # Verificar permisos para editar este usuario específico
    if not can_edit_target(request.user, user_to_update):
        messages.error(request, _('No tienes permiso para editar este usuario.'))
        return redirect('accounts:user_approval_dashboard')

    # PROTECCION: Super Admin solo modificable por codigo
    if user_to_update.is_super_admin():
        messages.error(request, _('El perfil de Super Admin solo puede modificarse por codigo.'))
        return redirect('accounts:admin_view_user', user_id)
    
    # PROTECCIÓN CRÍTICA: Evitar que Super Admin se desactive a sí mismo
    is_self_edit = (request.user.id == user_to_update.id)
    
    # Obtener datos del formulario
    # Soportar tanto first_name/last_name (nuevo formulario admin) como full_name (legacy)
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    full_name = request.POST.get('full_name', '').strip()
    
    company = request.POST.get('company', '').strip()
    role = request.POST.get('role', '')
    status = request.POST.get('status', '')
    email_verified = request.POST.get('email_verified') == 'on'
    is_active = request.POST.get('is_active') == 'on'
    
    # Determinar si viene del nuevo formulario admin
    is_admin_form = 'first_name' in request.POST
    redirect_view = 'accounts:admin_edit_user' if is_admin_form else 'accounts:user_approval_dashboard'
    
    # Validaciones
    if not full_name and not (first_name or last_name):
        messages.error(request, _('El nombre es obligatorio.'))
        if is_admin_form:
            return redirect('accounts:admin_edit_user', user_id)
        return redirect('accounts:user_approval_dashboard')
    
    if role and role not in dict(User.ROLE_CHOICES):
        messages.error(request, _('Rol inválido.'))
        if is_admin_form:
            return redirect('accounts:admin_edit_user', user_id)
        return redirect('accounts:user_approval_dashboard')
    
    # Validar permiso para asignar el role solicitado
    if role and role != user_to_update.role:
        if not can_assign_role(request.user, role):
            messages.error(request, _('No tienes permiso para asignar este rol.'))
            if is_admin_form:
                return redirect('accounts:admin_edit_user', user_id)
            return redirect('accounts:user_approval_dashboard')
    
    if status and status not in dict(User.STATUS_CHOICES):
        messages.error(request, _('Estado inválido.'))
        if is_admin_form:
            return redirect('accounts:admin_edit_user', user_id)
        return redirect('accounts:user_approval_dashboard')
    
    # Actualizar campos
    # Priorizar first_name/last_name sobre full_name
    if is_admin_form:
        user_to_update.first_name = first_name
        user_to_update.last_name = last_name
    elif full_name:
        user_to_update.full_name = full_name
    
    user_to_update.company = company
    if role:
        user_to_update.role = role
    
    # Manejar cambio de status
    if status:
        old_status = user_to_update.status
        
        # PROTECCIÓN CRÍTICA: Super Admin no puede desactivarse a sí mismo
        if is_self_edit and user_to_update.is_super_admin() and status != User.STATUS_ACTIVE:
            messages.error(
                request, 
                _('No puedes desactivar tu propia cuenta de Super Admin. Esto causaría pérdida de acceso a la plataforma.')
            )
            if is_admin_form:
                return redirect('accounts:admin_edit_user', user_id)
            return redirect('accounts:user_approval_dashboard')
        
        user_to_update.status = status
        
        # Sincronizar is_active con status
        user_to_update.is_active = (status == User.STATUS_ACTIVE)
        # Sincronizar pending_approval con status
        user_to_update.pending_approval = (status == User.STATUS_PENDING)
        
        # Si se cambia a ACTIVE (aprobación), registrar quién aprobó
        if status == User.STATUS_ACTIVE and old_status != User.STATUS_ACTIVE:
            if not user_to_update.approved_by:  # Solo si no tiene aprobador previo
                user_to_update.approved_by = request.user
                user_to_update.approved_at = timezone.now()
    
    user_to_update.email_verified = email_verified
    
    # Si viene del formulario legacy (no admin), usar is_active directamente
    if not is_admin_form and 'is_active' in request.POST:
        user_to_update.is_active = is_active
    
    user_to_update.save()
    
    messages.success(
        request,
        _('Usuario %(email)s actualizado correctamente.') % {'email': user_to_update.email}
    )
    
    # Si viene del formulario admin nuevo, redirigir a vista de perfil
    if is_admin_form:
        return redirect('accounts:admin_view_user', user_id)
    else:
        return redirect('accounts:user_approval_dashboard')


@login_required
@admin_required
@require_POST
def user_delete_view(request, user_id):
    """
    Elimina un usuario (hard delete).
    
    RBAC:
    - SUPER_ADMIN puede eliminar cualquiera (excepto a sí mismo)
    - ADMIN puede eliminar user y admin, pero NO super_admin
    """
    user_to_delete = get_object_or_404(User, pk=user_id)
    
    # Verificar permisos para eliminar este usuario
    if not can_delete_target(request.user, user_to_delete):
        messages.error(request, _('No tienes permiso para eliminar este usuario.'))
        return redirect('accounts:user_approval_dashboard')
    
    if settings.ALLOW_HARD_DELETE:
        user_email = user_to_delete.email
        user_to_delete.delete()
        result_message = _(
            'Usuario %(email)s eliminado físicamente.'
        ) % {'email': user_email}
    else:
        from accounts.models import UserSession
        from core.audit import AuditLog

        user_to_delete.status = User.STATUS_DISABLED
        user_to_delete.pending_approval = False
        user_to_delete.is_active = False
        user_to_delete.save(update_fields=[
            'status', 'pending_approval', 'is_active', 'updated_at',
        ])
        UserSession.objects.filter(
            user=user_to_delete,
            is_active=True,
        ).update(is_active=False)
        AuditLog.log(
            user=request.user,
            action=AuditLog.ACTION_USER_DISABLED,
            description='Cuenta desactivada por un administrador; no se realizó borrado físico.',
            object_type='User',
            object_id=user_to_delete.pk,
            request=request,
        )
        result_message = _(
            'Usuario %(email)s desactivado. Sus datos no se han eliminado físicamente.'
        ) % {'email': user_to_delete.email}
    
    messages.success(
        request,
        result_message
    )
    return redirect('accounts:user_approval_dashboard')


@login_required
@admin_required
@require_POST
@transaction.atomic
def user_status_view(request, user_id):
    """Activa o desactiva una cuenta con bloqueo transaccional y auditoría."""
    from accounts.models import UserSession
    from core.audit import AuditLog

    target = get_object_or_404(
        User.objects.select_for_update(),
        pk=user_id,
    )
    if not can_edit_target(request.user, target):
        return _json_error(
            _('No tienes permiso para modificar este usuario.'),
            status=403,
        )

    requested_status = request.POST.get('status', '').strip()
    if requested_status not in (User.STATUS_ACTIVE, User.STATUS_DISABLED):
        return _json_error(_('Estado solicitado no válido.'), status=400)

    if target.pk == request.user.pk and requested_status != User.STATUS_ACTIVE:
        return _json_error(
            _('No puedes desactivar tu propia cuenta.'),
            status=409,
        )

    if target.is_super_admin() and requested_status != User.STATUS_ACTIVE:
        remaining_super_admins = (
            User.objects.select_for_update()
            .filter(
                role=User.ROLE_SUPER_ADMIN,
                status=User.STATUS_ACTIVE,
                is_active=True,
            )
            .exclude(pk=target.pk)
            .count()
        )
        if remaining_super_admins == 0:
            return _json_error(
                _('No se puede desactivar al último superadministrador.'),
                status=409,
            )

    if target.status == requested_status:
        return _json_error(
            _('El usuario ya tiene ese estado.'),
            status=409,
        )

    target.status = requested_status
    target.pending_approval = False
    target.is_active = requested_status == User.STATUS_ACTIVE
    target.save(update_fields=[
        'status',
        'pending_approval',
        'is_active',
        'updated_at',
    ])

    if requested_status == User.STATUS_DISABLED:
        UserSession.objects.filter(
            user=target,
            is_active=True,
        ).update(is_active=False)
        audit_action = AuditLog.ACTION_USER_DISABLED
        description = 'Cuenta desactivada desde Gestión de Usuarios.'
        message = _(
            'Usuario %(email)s desactivado correctamente.'
        ) % {'email': target.email}
    else:
        audit_action = 'user_reactivated'
        description = 'Cuenta reactivada desde Gestión de Usuarios.'
        message = _(
            'Usuario %(email)s activado correctamente.'
        ) % {'email': target.email}

    AuditLog.log(
        user=request.user,
        action=audit_action,
        description=description,
        object_type='User',
        object_id=target.pk,
        request=request,
    )
    return JsonResponse({
        'ok': True,
        'message': message,
        'user': {
            'id': target.pk,
            'status': target.status,
            'status_label': target.get_status_display(),
            'is_active': target.is_active,
        },
        'counts': _management_counts(request.user),
    })


@login_required
@admin_required
@require_POST
def admin_password_reset_view(request, user_id):
    """Envía el enlace oficial de restablecimiento sin exponer contraseñas."""
    from django.contrib.auth.forms import PasswordResetForm
    from core.audit import AuditLog

    target = get_object_or_404(User, pk=user_id)
    if not can_edit_target(request.user, target):
        return _json_error(
            _('No tienes permiso para modificar este usuario.'),
            status=403,
        )
    if not target.is_active:
        return _json_error(
            _('Activa la cuenta antes de enviar un restablecimiento.'),
            status=409,
        )

    form = PasswordResetForm({'email': target.email})
    if not form.is_valid():
        return _json_error(
            _('No se pudo iniciar el restablecimiento de contraseña.'),
            status=400,
        )

    try:
        form.save(
            request=request,
            use_https=request.is_secure(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            subject_template_name='accounts/password_reset_subject.txt',
            email_template_name='accounts/password_reset_email.html',
        )
    except Exception:
        return _json_error(
            _(
                'No se pudo enviar el enlace de restablecimiento. '
                'Inténtalo de nuevo.'
            ),
            status=502,
        )

    AuditLog.log(
        user=request.user,
        action='password_reset_requested',
        description='Enlace de restablecimiento solicitado por un administrador.',
        object_type='User',
        object_id=target.pk,
        request=request,
    )
    return JsonResponse({
        'ok': True,
        'message': _(
            'Se ha enviado el enlace de restablecimiento a %(email)s.'
        ) % {'email': target.email},
    })


@login_required
@admin_required
@require_POST
@transaction.atomic
def approve_user_view(request, user_id):
    """
    Aprueba un nuevo usuario pendiente.
    Cambia status='active', activa acceso, envía email de notificación.
    
    IMPORTANTE: El role NO cambia automáticamente (sigue siendo 'user').
    """
    from core.audit import AuditLog

    user_to_approve = get_object_or_404(
        User.objects.select_for_update(),
        pk=user_id,
    )
    if not can_edit_target(request.user, user_to_approve):
        if _wants_json(request):
            return _json_error(
                _('No tienes permiso para aprobar este usuario.'),
                status=403,
            )
        messages.error(request, _('No tienes permiso para aprobar este usuario.'))
        return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")
    
    # Solo se pueden aprobar usuarios con status='pending'
    if user_to_approve.status != User.STATUS_PENDING:
        if _wants_json(request):
            return _json_error(_('Este usuario ya fue procesado.'), status=409)
        messages.warning(request, _('Este usuario ya fue procesado.'))
        return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")
    
    # Cambiar estado a activo (el role permanece como 'user')
    user_to_approve.status = User.STATUS_ACTIVE
    user_to_approve.pending_approval = False
    user_to_approve.is_active = True
    user_to_approve.email_verified = True  # Asegurar que está verificado
    user_to_approve.approved_by = request.user
    user_to_approve.approved_at = timezone.now()
    user_to_approve.save()
    AuditLog.log(
        user=request.user,
        action=AuditLog.ACTION_USER_APPROVED,
        description='Solicitud de usuario aprobada desde Gestión de Usuarios.',
        object_type='User',
        object_id=user_to_approve.pk,
        request=request,
    )
    
    # Enviar email al usuario
    warning = ''
    try:
        from .utils import send_user_approved_email
        send_user_approved_email(user_to_approve, request)
    except Exception:
        warning = _(
            'El usuario fue aprobado, pero no se pudo enviar la notificación.'
        )

    success_message = _(
        'Usuario %(email)s aprobado correctamente.'
    ) % {'email': user_to_approve.email}
    if _wants_json(request):
        return JsonResponse({
            'ok': True,
            'message': success_message,
            'warning': warning,
            'user': {
                'id': user_to_approve.pk,
                'status': user_to_approve.status,
                'status_label': user_to_approve.get_status_display(),
            },
            'counts': _management_counts(request.user),
        })

    if warning:
        messages.warning(request, f'{success_message} {warning}')
    else:
        messages.success(request, success_message)
    
    return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")


@login_required
@admin_required
@require_POST
@transaction.atomic
def update_pending_request(request):
    """
    Actualiza estado/rol/email_verificado de una solicitud pendiente.
    Permite aprobación manual incluso sin verificación previa.
    """
    user_id = request.POST.get('user_id')
    status = request.POST.get('status')
    role = request.POST.get('role')
    email_verified = request.POST.get('email_verified') == 'on'
    full_name = request.POST.get('full_name', '').strip()
    company = request.POST.get('company', '').strip()

    user_to_update = get_object_or_404(
        User.objects.select_for_update(),
        pk=user_id,
    )

    if not can_edit_target(request.user, user_to_update):
        if _wants_json(request):
            return _json_error(
                _('No tienes permiso para editar este usuario.'),
                status=403,
            )
        messages.error(request, _('No tienes permiso para editar este usuario.'))
        return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")

    if user_to_update.status != User.STATUS_PENDING:
        if _wants_json(request):
            return _json_error(_('Esta solicitud ya fue procesada.'), status=409)
        messages.warning(request, _('Esta solicitud ya fue procesada.'))
        return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")

    # La edición de una solicitud no debe saltarse los flujos auditados de
    # aprobación o rechazo. Esas transiciones tienen endpoints dedicados.
    if status != User.STATUS_PENDING:
        if _wants_json(request):
            return _json_error(
                _('Para aprobar o rechazar utiliza la acción correspondiente.'),
                status=400,
            )
        messages.error(
            request,
            _('Para aprobar o rechazar utiliza la acción correspondiente.'),
        )
        return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")

    if role and role not in dict(User.ROLE_CHOICES):
        if _wants_json(request):
            return _json_error(_('Rol inválido.'), status=400)
        messages.error(request, _('Rol inválido.'))
        return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")

    if role and role != user_to_update.role:
        if not can_assign_role(request.user, role):
            if _wants_json(request):
                return _json_error(
                    _('No tienes permiso para asignar este rol.'),
                    status=403,
                )
            messages.error(request, _('No tienes permiso para asignar este rol.'))
            return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")

    if not full_name:
        if _wants_json(request):
            return _json_error(_('El nombre es obligatorio.'), status=400)
        messages.error(request, _('El nombre es obligatorio.'))
        return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")

    user_to_update.full_name = full_name[:200]
    user_to_update.company = company[:200]
    user_to_update.status = status
    if role:
        user_to_update.role = role

    if status == User.STATUS_ACTIVE:
        user_to_update.pending_approval = False
        user_to_update.is_active = True
        user_to_update.approved_by = request.user
        user_to_update.approved_at = timezone.now()
        user_to_update.email_verified = True
    elif status in (User.STATUS_REJECTED, User.STATUS_DISABLED):
        user_to_update.pending_approval = False
        user_to_update.is_active = False
        user_to_update.email_verified = email_verified
    else:
        user_to_update.pending_approval = True
        user_to_update.is_active = True
        user_to_update.email_verified = email_verified

    user_to_update.save()

    # Send appropriate email based on status change
    if status == User.STATUS_ACTIVE:
        try:
            from .utils import send_user_approved_email
            send_user_approved_email(user_to_update, request)
        except Exception as e:
            if _wants_json(request):
                return JsonResponse({
                    'ok': True,
                    'message': _('Solicitud actualizada correctamente.'),
                    'warning': _(
                        'No se pudo enviar el email de notificación.'
                    ),
                    'counts': _management_counts(request.user),
                })
            messages.warning(request, _('Usuario actualizado pero no se pudo enviar email: %(error)s') % {'error': str(e)})
            return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")
    elif status == User.STATUS_REJECTED:
        try:
            from .utils import send_user_rejected_email
            send_user_rejected_email(user_to_update, request)
        except Exception as e:
            if _wants_json(request):
                return JsonResponse({
                    'ok': True,
                    'message': _('Solicitud actualizada correctamente.'),
                    'warning': _(
                        'No se pudo enviar el email de notificación.'
                    ),
                    'counts': _management_counts(request.user),
                })
            messages.warning(request, _('Usuario rechazado pero no se pudo enviar email: %(error)s') % {'error': str(e)})
            return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")

    if _wants_json(request):
        return JsonResponse({
            'ok': True,
            'message': _('Solicitud actualizada correctamente.'),
            'user': {
                'id': user_to_update.pk,
                'full_name': user_to_update.full_name,
                'company': user_to_update.company,
                'role': user_to_update.role,
                'role_label': user_to_update.get_role_display(),
                'status': user_to_update.status,
                'status_label': user_to_update.get_status_display(),
            },
            'counts': _management_counts(request.user),
        })

    messages.success(request, _('Solicitud actualizada correctamente.'))
    return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")


@login_required
@admin_required
@require_POST
@transaction.atomic
def reject_user_view(request, user_id):
    """
    Rechaza un nuevo usuario pendiente.
    Cambia status='rejected', desactiva acceso, envía email de notificación.
    """
    from core.audit import AuditLog

    user_to_reject = get_object_or_404(
        User.objects.select_for_update(),
        pk=user_id,
    )
    if not can_edit_target(request.user, user_to_reject):
        if _wants_json(request):
            return _json_error(
                _('No tienes permiso para rechazar este usuario.'),
                status=403,
            )
        messages.error(request, _('No tienes permiso para rechazar este usuario.'))
        return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")
    
    # Solo se pueden rechazar usuarios con status='pending'
    if user_to_reject.status != User.STATUS_PENDING:
        if _wants_json(request):
            return _json_error(_('Este usuario ya fue procesado.'), status=409)
        messages.warning(request, _('Este usuario ya fue procesado.'))
        return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")
    
    # Cambiar estado a rechazado
    user_to_reject.status = User.STATUS_REJECTED
    user_to_reject.pending_approval = False
    user_to_reject.is_active = False
    user_to_reject.save()
    AuditLog.log(
        user=request.user,
        action=AuditLog.ACTION_USER_REJECTED,
        description='Solicitud de usuario rechazada desde Gestión de Usuarios.',
        object_type='User',
        object_id=user_to_reject.pk,
        request=request,
    )
    
    # Enviar email al usuario
    warning = ''
    try:
        from .utils import send_user_rejected_email
        send_user_rejected_email(user_to_reject, request)
    except Exception:
        warning = _(
            'La solicitud fue rechazada, pero no se pudo enviar la notificación.'
        )

    success_message = _(
        'Solicitud de %(email)s rechazada correctamente.'
    ) % {'email': user_to_reject.email}
    if _wants_json(request):
        return JsonResponse({
            'ok': True,
            'message': success_message,
            'warning': warning,
            'user': {
                'id': user_to_reject.pk,
                'status': user_to_reject.status,
                'status_label': user_to_reject.get_status_display(),
            },
            'counts': _management_counts(request.user),
        })

    if warning:
        messages.warning(request, f'{success_message} {warning}')
    else:
        messages.success(request, success_message)
    
    return redirect(f"{reverse('accounts:user_approval_dashboard')}?tab=pending")


# Vista antigua de user_approve eliminada - usar approve_user_view y reject_user_view
