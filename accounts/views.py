from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
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


@login_required
def dashboard_view(request):
    """Vista principal del Dashboard/Inicio de Fénix"""
    from orders.models import Order
    from notifications.models import Notification
    
    user = request.user
    
    # Mis Pedidos (Order usa 'customer' no 'user')
    active_orders = Order.objects.filter(customer=user, status__in=['pending', 'processing']).count()
    pending_orders = Order.objects.filter(customer=user, status='pending').count()
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
        'active_orders_count': active_orders,
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
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Verificar si es admin (pueden entrar aunque tengan pending_approval)
            is_admin = is_manager_or_admin(user)
            
            if not user.is_active:
                messages.error(request, _('Tu cuenta está desactivada.'))
            elif not user.email_verified:
                # Redirigir a página de verificación de email
                request.session['unverified_user_email'] = user.email
                messages.warning(request, _('Debes verificar tu email antes de iniciar sesión.'))
                return redirect('accounts:email_verification')
            elif user.pending_approval and not is_admin:
                messages.warning(request, _('Tu cuenta está pendiente de aprobación por un administrador.'))
                return redirect('accounts:pending_approval')
            else:
                login(request, user)
                messages.success(request, _('Bienvenido, %(name)s!') % {'name': user.full_name})
                next_url = request.GET.get('next')
                if next_url:
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
            
            # Enviar email de verificación con token
            try:
                verification_url = request.build_absolute_uri('/accounts/verify-email/')
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
    return render(request, 'accounts/pending_approval.html')


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
        
        messages.success(request, _('¡Email verificado exitosamente! Ahora puedes iniciar sesión.'))
        return redirect('accounts:login')
        
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
        verification_url = request.build_absolute_uri('/accounts/verify-email/')
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
def user_approval_list(request):
    """
    Vista MEJORADA: Dashboard de gestión de usuarios con 2 pestañas.
    TAB 1: Usuarios registrados (CRUD completo) - NO incluye pendientes
    TAB 2: Nuevos usuarios pendientes (aprobación) - SOLO pendientes
    
    RBAC:
    - SUPER_ADMIN ve todos los usuarios
    - ADMIN ve todos EXCEPTO super_admin
    """
    # Base queryset de usuarios registrados (no pending)
    base_registered = User.objects.filter(
        status__in=[User.STATUS_ACTIVE, User.STATUS_DISABLED, User.STATUS_REJECTED]
    )
    
    # Filtrar según rol del usuario logado
    registered_users = get_visible_users_queryset(request.user, base_registered)
    registered_users = registered_users.order_by('-date_joined')
    
    # Filtros para TAB 1
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    if status_filter and status_filter in [User.STATUS_ACTIVE, User.STATUS_DISABLED, User.STATUS_REJECTED]:
        registered_users = registered_users.filter(status=status_filter)
    
    if search_query:
        registered_users = registered_users.filter(
            Q(email__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(company__icontains=search_query)
        )
    
    # TAB 2: SOLO nuevos usuarios pendientes (status='pending' y role='user')
    # Los pending solo deberían ser users, no admin ni super_admin
    pending_new_users = User.objects.filter(
        status=User.STATUS_PENDING,
        role=User.ROLE_USER  # Solo mostrar users en aprobación
    ).order_by('-date_joined')
    
    # Obtener opciones de roles que el usuario puede asignar
    available_role_choices = get_role_choices_for_user(request.user)
    
    context = {
        'registered_users': registered_users,
        'pending_new_users': pending_new_users,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': [
            (User.STATUS_ACTIVE, _('Activo')),
            (User.STATUS_DISABLED, _('Deshabilitado')),
            (User.STATUS_REJECTED, _('Rechazado')),
        ],
        'available_role_choices': available_role_choices,
        'active_tab': request.GET.get('tab', 'registered'),
        'user_is_super_admin': request.user.is_super_admin(),
    }
    return render(request, 'accounts/user_approval_dashboard.html', context)


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
    
    # Obtener datos del formulario
    full_name = request.POST.get('full_name', '').strip()
    company = request.POST.get('company', '').strip()
    role = request.POST.get('role', '')
    status = request.POST.get('status', '')
    email_verified = request.POST.get('email_verified') == 'on'
    is_active = request.POST.get('is_active') == 'on'
    
    # Validaciones
    if not full_name:
        messages.error(request, _('El nombre completo es obligatorio.'))
        return redirect('accounts:user_approval_dashboard')
    
    if role and role not in dict(User.ROLE_CHOICES):
        messages.error(request, _('Rol inválido.'))
        return redirect('accounts:user_approval_dashboard')
    
    # Validar permiso para asignar el role solicitado
    if role and role != user_to_update.role:
        if not can_assign_role(request.user, role):
            messages.error(request, _('No tienes permiso para asignar este rol.'))
            return redirect('accounts:user_approval_dashboard')
    
    if status not in dict(User.STATUS_CHOICES):
        messages.error(request, _('Estado inválido.'))
        return redirect('accounts:user_approval_dashboard')
    
    # Actualizar campos
    user_to_update.full_name = full_name
    user_to_update.company = company
    if role:
        user_to_update.role = role
    user_to_update.status = status
    user_to_update.email_verified = email_verified
    user_to_update.is_active = is_active
    
    # Sincronizar pending_approval con status
    user_to_update.pending_approval = (status == User.STATUS_PENDING)
    
    user_to_update.save()
    
    messages.success(
        request,
        _('Usuario %(email)s actualizado correctamente.') % {'email': user_to_update.email}
    )
    return redirect('accounts:user_approval_dashboard')


@login_required
@admin_required
@require_POST
def user_delete_view(request, user_id):
    """
    Elimina un usuario (soft delete cambiando status a disabled).
    
    RBAC:
    - SUPER_ADMIN puede eliminar cualquiera (excepto a sí mismo)
    - ADMIN puede eliminar user y admin, pero NO super_admin
    """
    user_to_delete = get_object_or_404(User, pk=user_id)
    
    # Verificar permisos para eliminar este usuario
    if not can_delete_target(request.user, user_to_delete):
        messages.error(request, _('No tienes permiso para eliminar este usuario.'))
        return redirect('accounts:user_approval_dashboard')
    
    # Soft delete: cambiar status y desactivar
    user_to_delete.status = User.STATUS_DISABLED
    user_to_delete.is_active = False
    user_to_delete.save()
    
    messages.success(
        request,
        _('Usuario %(email)s deshabilitado correctamente.') % {'email': user_to_delete.email}
    )
    return redirect('accounts:user_approval_dashboard')


@login_required
@admin_required
@require_POST
def approve_user_view(request, user_id):
    """
    Aprueba un nuevo usuario pendiente.
    Cambia status='active', activa acceso, envía email de notificación.
    
    IMPORTANTE: El role NO cambia automáticamente (sigue siendo 'user').
    """
    user_to_approve = get_object_or_404(User, pk=user_id)
    
    # Solo se pueden aprobar usuarios con status='pending'
    if user_to_approve.status != User.STATUS_PENDING:
        messages.warning(request, _('Este usuario ya fue procesado.'))
        return redirect('accounts:user_approval_dashboard' + '?tab=new_users')
    
    # Cambiar estado a activo (el role permanece como 'user')
    user_to_approve.status = User.STATUS_ACTIVE
    user_to_approve.pending_approval = False
    user_to_approve.is_active = True
    user_to_approve.email_verified = True  # Asegurar que está verificado
    user_to_approve.approved_by = request.user
    user_to_approve.approved_at = timezone.now()
    user_to_approve.save()
    
    # Enviar email al usuario
    try:
        from .utils import send_user_approved_email
        send_user_approved_email(user_to_approve, request)
        messages.success(
            request,
            _('Usuario %(email)s aprobado exitosamente. Se ha enviado un email de notificación.') % 
            {'email': user_to_approve.email}
        )
    except Exception as e:
        messages.warning(
            request,
            _('Usuario %(email)s aprobado, pero hubo un error al enviar el email: %(error)s') % 
            {'email': user_to_approve.email, 'error': str(e)}
        )
    
    return redirect('accounts:user_approval_dashboard' + '?tab=new_users')


@login_required
@admin_required
@require_POST
def reject_user_view(request, user_id):
    """
    Rechaza un nuevo usuario pendiente.
    Cambia status='rejected', desactiva acceso, envía email de notificación.
    """
    user_to_reject = get_object_or_404(User, pk=user_id)
    
    # Solo se pueden rechazar usuarios con status='pending'
    if user_to_reject.status != User.STATUS_PENDING:
        messages.warning(request, _('Este usuario ya fue procesado.'))
        return redirect('accounts:user_approval_dashboard' + '?tab=new_users')
    
    # Cambiar estado a rechazado
    user_to_reject.status = User.STATUS_REJECTED
    user_to_reject.pending_approval = False
    user_to_reject.is_active = False
    user_to_reject.save()
    
    # Enviar email al usuario
    try:
        from .utils import send_user_rejected_email
        send_user_rejected_email(user_to_reject, request)
        messages.success(
            request,
            _('Solicitud de %(email)s rechazada. Se ha enviado un email de notificación.') % 
            {'email': user_to_reject.email}
        )
    except Exception as e:
        messages.warning(
            request,
            _('Solicitud rechazada, pero hubo un error al enviar el email: %(error)s') % 
            {'error': str(e)}
        )
    
    return redirect('accounts:user_approval_dashboard' + '?tab=new_users')


# Vista antigua de user_approve eliminada - usar approve_user_view y reject_user_view
