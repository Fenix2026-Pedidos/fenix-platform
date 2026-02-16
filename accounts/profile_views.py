import secrets
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from .models import User, UserSession, LoginHistory, ProfileAuditLog, SecuritySettings
from .profile_forms import (
    PersonalDataForm, CompanyDataForm, PreferencesForm,
    SecurityForm, PasswordChangeForm, AvatarUploadForm, OperativeProfileForm
)
from organizations.models import UserCompany
from core.audit import log_action


def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_profile_action(user, action, field_changed=None, old_value=None, new_value=None, request=None):
    """Registrar acción en el log de auditoría del perfil"""
    ProfileAuditLog.objects.create(
        user=user,
        action=action,
        field_changed=field_changed or '',
        old_value=str(old_value) if old_value else '',
        new_value=str(new_value) if new_value else '',
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )


@login_required
def profile_dashboard(request):
    """Vista principal del perfil del usuario"""
    user = request.user
    
    # Obtener o crear preferencias y configuración de seguridad
    preferences = user.get_or_create_preferences()
    security = user.get_or_create_security()
    
    # Obtener relación con empresa
    user_company = UserCompany.objects.filter(
        user=user, 
        is_active=True
    ).select_related('company').first()
    
    # Obtener sesiones activas
    active_sessions = UserSession.objects.filter(
        user=user,
        is_active=True,
        expires_at__gt=timezone.now()
    ).order_by('-last_activity')[:5]
    
    # Obtener últimos inicios de sesión
    recent_logins = LoginHistory.objects.filter(
        user=user
    ).order_by('-created_at')[:10]
    
    # Detectar campos obligatorios faltantes
    required_fields = [
        'telefono_reparto',
        'direccion_local',
        'ciudad',
        'provincia',
        'codigo_postal',
        'tipo_entrega',
        'direccion_entrega',
        'ciudad_entrega',
        'provincia_entrega',
        'codigo_postal_entrega',
    ]
    
    missing_fields = []
    for field in required_fields:
        value = getattr(user, field, None)
        if not value or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)
    
    context = {
        'user': user,
        'preferences': preferences,
        'security': security,
        'user_company': user_company,
        'active_sessions': active_sessions,
        'recent_logins': recent_logins,
        'session_count': active_sessions.count(),
        'edit_mode': False,
        'missing_fields': missing_fields,
    }
    
    return render(request, 'accounts/profile/profile_dashboard_new.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def update_personal_data(request):
    """Actualizar datos personales del usuario"""
    if request.method == 'POST':
        form = PersonalDataForm(request.POST, instance=request.user)
        if form.is_valid():
            old_values = {
                field: getattr(request.user, field)
                for field in form.changed_data
            }
            
            user = form.save()
            
            # Registrar cambios en el log
            for field in form.changed_data:
                log_profile_action(
                    user=user,
                    action='update_personal',
                    field_changed=field,
                    old_value=old_values.get(field),
                    new_value=getattr(user, field),
                    request=request
                )
            
            messages.success(request, _('Datos personales actualizados correctamente'))
            return redirect('accounts:profile_dashboard')
    else:
        form = PersonalDataForm(instance=request.user)
    
    return render(request, 'accounts/profile/edit_personal.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def update_company_data(request):
    """Actualizar datos de empresa del usuario"""
    user_company = get_object_or_404(
        UserCompany,
        user=request.user,
        is_active=True
    )
    
    if request.method == 'POST':
        form = CompanyDataForm(request.POST, instance=user_company)
        if form.is_valid():
            old_values = {
                field: getattr(user_company, field)
                for field in form.changed_data
            }
            
            user_company = form.save()
            
            # Registrar cambios en el log
            for field in form.changed_data:
                log_profile_action(
                    user=request.user,
                    action='update_company',
                    field_changed=field,
                    old_value=old_values.get(field),
                    new_value=getattr(user_company, field),
                    request=request
                )
            
            messages.success(request, _('Datos de empresa actualizados correctamente'))
            return redirect('accounts:profile_dashboard')
    else:
        form = CompanyDataForm(instance=user_company)
    
    return render(request, 'accounts/profile/edit_company.html', {
        'form': form,
        'user_company': user_company
    })


@login_required
@require_http_methods(['GET', 'POST'])
def update_preferences(request):
    """Actualizar preferencias del usuario"""
    preferences = request.user.get_or_create_preferences()
    
    if request.method == 'POST':
        form = PreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            old_values = {
                field: getattr(preferences, field)
                for field in form.changed_data
            }
            
            preferences = form.save()
            
            # Registrar cambios en el log
            for field in form.changed_data:
                log_profile_action(
                    user=request.user,
                    action='update_preferences',
                    field_changed=field,
                    old_value=old_values.get(field),
                    new_value=getattr(preferences, field),
                    request=request
                )
            
            messages.success(request, _('Preferencias actualizadas correctamente'))
            return redirect('accounts:profile_dashboard')
    else:
        form = PreferencesForm(instance=preferences)
    
    return render(request, 'accounts/profile/edit_preferences.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def update_security(request):
    """Actualizar configuración de seguridad"""
    security = request.user.get_or_create_security()
    
    if request.method == 'POST':
        form = SecurityForm(request.POST, instance=security)
        if form.is_valid():
            old_values = {
                field: getattr(security, field)
                for field in form.changed_data
            }
            
            security = form.save()
            
            # Registrar cambios en el log
            for field in form.changed_data:
                log_profile_action(
                    user=request.user,
                    action='update_security',
                    field_changed=field,
                    old_value=old_values.get(field),
                    new_value=getattr(security, field),
                    request=request
                )
            
            messages.success(request, _('Configuración de seguridad actualizada'))
            return redirect('accounts:profile_dashboard')
    else:
        form = SecurityForm(instance=security)
    
    return render(request, 'accounts/profile/edit_security.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def change_password(request):
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            
            # Actualizar fecha de cambio de contraseña
            security = user.get_or_create_security()
            security.password_changed_at = timezone.now()
            security.save(update_fields=['password_changed_at'])
            
            # Mantener sesión activa
            update_session_auth_hash(request, user)
            
            # Registrar en el log
            log_profile_action(
                user=user,
                action='change_password',
                request=request
            )
            
            messages.success(request, _('Contraseña cambiada correctamente'))
            return redirect('accounts:profile_dashboard')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/profile/change_password.html', {'form': form})


@login_required
@require_POST
def enable_2fa(request):
    """Habilitar autenticación de dos factores"""
    security = request.user.get_or_create_security()
    
    if not security.two_factor_enabled:
        security.two_factor_enabled = True
        security.two_factor_method = request.POST.get('method', 'totp')
        security.two_factor_secret = secrets.token_urlsafe(32)
        security.save()
        
        log_profile_action(
            user=request.user,
            action='enable_2fa',
            field_changed='two_factor_method',
            new_value=security.two_factor_method,
            request=request
        )
        
        messages.success(request, _('Autenticación de dos factores habilitada'))
    
    return redirect('accounts:profile_dashboard')


@login_required
@require_POST
def disable_2fa(request):
    """Deshabilitar autenticación de dos factores"""
    security = request.user.get_or_create_security()
    
    if security.two_factor_enabled:
        security.two_factor_enabled = False
        security.two_factor_secret = None
        security.save()
        
        log_profile_action(
            user=request.user,
            action='disable_2fa',
            request=request
        )
        
        messages.success(request, _('Autenticación de dos factores deshabilitada'))
    
    return redirect('accounts:profile_dashboard')


@login_required
def active_sessions(request):
    """Ver sesiones activas"""
    sessions = UserSession.objects.filter(
        user=request.user,
        is_active=True,
        expires_at__gt=timezone.now()
    ).order_by('-last_activity')
    
    # Marcar la sesión actual
    current_session_key = request.session.session_key
    
    context = {
        'sessions': sessions,
        'current_session_key': current_session_key,
    }
    
    return render(request, 'accounts/profile/active_sessions.html', context)


@login_required
@require_POST
def revoke_session(request, session_id):
    """Revocar una sesión específica"""
    session = get_object_or_404(
        UserSession,
        id=session_id,
        user=request.user
    )
    
    # No permitir revocar la sesión actual
    if session.session_key != request.session.session_key:
        session.is_active = False
        session.save()
        messages.success(request, _('Sesión revocada correctamente'))
    else:
        messages.error(request, _('No puedes revocar tu sesión actual'))
    
    return redirect('accounts:active_sessions')


@login_required
@require_POST
def revoke_all_sessions(request):
    """Revocar todas las sesiones excepto la actual"""
    UserSession.objects.filter(
        user=request.user,
        is_active=True
    ).exclude(
        session_key=request.session.session_key
    ).update(is_active=False)
    
    messages.success(request, _('Todas las demás sesiones han sido revocadas'))
    return redirect('accounts:active_sessions')


@login_required
@require_http_methods(['GET', 'POST'])
def upload_avatar(request):
    """Subir foto de perfil del usuario"""
    if request.method == 'POST':
        form = AvatarUploadForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Guardar valor anterior antes de eliminar
            old_avatar_name = request.user.avatar.name if request.user.avatar else ''
            
            # Eliminar avatar anterior si existe
            if request.user.avatar:
                try:
                    request.user.avatar.delete(save=False)
                except Exception:
                    pass  # Si falla al eliminar, continuar igualmente
            
            user = form.save()
            
            log_profile_action(
                user=user,
                action='avatar_upload',
                field_changed='avatar',
                old_value=old_avatar_name,
                new_value=user.avatar.name if user.avatar else '',
                request=request
            )
            
            messages.success(request, _('Foto de perfil actualizada correctamente'))
            return redirect('accounts:profile_dashboard')
    else:
        form = AvatarUploadForm(instance=request.user)
    
    return render(request, 'accounts/profile/upload_avatar.html', {'form': form})


@login_required
@require_POST
def delete_avatar(request):
    """Eliminar foto de perfil del usuario"""
    if request.user.avatar:
        old_avatar_name = request.user.avatar.name
        request.user.avatar.delete(save=True)
        
        log_profile_action(
            user=request.user,
            action='avatar_delete',
            field_changed='avatar',
            old_value=old_avatar_name,
            new_value='',
            request=request
        )
        
        messages.success(request, _('Foto de perfil eliminada correctamente'))
    
    return redirect('accounts:profile_dashboard')


@login_required
def login_history(request):
    """Ver historial de inicios de sesión"""
    history = LoginHistory.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Paginación
    paginator = Paginator(history, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'accounts/profile/login_history.html', context)


@login_required
def audit_log(request):
    """Ver log de auditoría del perfil"""
    logs = ProfileAuditLog.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Filtros
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    # Paginación
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_filter': action,
        'action_choices': ProfileAuditLog.ACTION_CHOICES,
    }
    
    return render(request, 'accounts/profile/audit_log.html', context)


@login_required
@require_POST
def generate_api_token(request):
    """Generar nuevo token de API"""
    security = request.user.get_or_create_security()
    
    # Generar nuevo token
    security.api_token = secrets.token_urlsafe(32)
    security.api_token_created_at = timezone.now()
    security.save()
    
    messages.success(request, _('Token de API generado correctamente'))
    return redirect('accounts:profile_dashboard')


@login_required
@require_POST
def revoke_api_token(request):
    """Revocar token de API"""
    security = request.user.get_or_create_security()
    
    if security.api_token:
        security.api_token = None
        security.api_token_created_at = None
        security.api_token_last_used = None
        security.save()
        
        messages.success(request, _('Token de API revocado correctamente'))
    
    return redirect('accounts:profile_dashboard')


@login_required
@require_http_methods(['GET', 'POST'])
def update_operative_profile(request):
    """Actualizar perfil operativo del usuario"""
    user = request.user
    
    if request.method == 'POST':
        form = OperativeProfileForm(request.POST, instance=user)
        if form.is_valid():
            old_values = {
                field: getattr(user, field)
                for field in form.changed_data
            }
            
            user = form.save()
            
            # Registrar cambios en el log
            for field in form.changed_data:
                log_profile_action(
                    user=user,
                    action='update_operative_profile',
                    field_changed=field,
                    old_value=old_values.get(field),
                    new_value=getattr(user, field),
                    request=request
                )
            
            messages.success(request, _('Perfil operativo actualizado correctamente'))
            return redirect('accounts:profile_dashboard')
    else:
        form = OperativeProfileForm(instance=user)
    
    return render(request, 'accounts/profile/edit_operative.html', {
        'form': form,
        'user': user
    })


@login_required
def operative_profile_edit(request):
    """Alias para compatibility - redirige a update_operative_profile"""
    return update_operative_profile(request)

@login_required
@require_http_methods(['GET', 'POST'])
def update_complete_profile(request):
    """Actualizar perfil completo del usuario (datos personales + perfil operativo)"""
    user = request.user
    
    if request.method == 'POST':
        # Actualizar todos los campos del formulario
        # Datos personales
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.company = request.POST.get('company', '').strip()
        user.phone = request.POST.get('phone', '').strip()
        
        # Contacto operativo
        user.telefono_empresa = request.POST.get('telefono_empresa', '').strip()
        user.telefono_reparto = request.POST.get('telefono_reparto', '').strip()
        
        # Dirección local/fiscal
        user.direccion_local = request.POST.get('direccion_local', '').strip()
        user.ciudad = request.POST.get('ciudad', '').strip()
        user.provincia = request.POST.get('provincia', '').strip()
        user.codigo_postal = request.POST.get('codigo_postal', '').strip()
        user.pais = request.POST.get('pais', 'España').strip()
        
        # Dirección de entrega
        user.tipo_entrega = request.POST.get('tipo_entrega', '').strip()
        user.direccion_entrega = request.POST.get('direccion_entrega', '').strip()
        user.ciudad_entrega = request.POST.get('ciudad_entrega', '').strip()
        user.provincia_entrega = request.POST.get('provincia_entrega', '').strip()
        user.codigo_postal_entrega = request.POST.get('codigo_postal_entrega', '').strip()
        user.ventana_entrega = request.POST.get('ventana_entrega', '').strip()
        user.observaciones_entrega = request.POST.get('observaciones_entrega', '').strip()
        
        # Validar campos obligatorios
        required_fields = {
            'telefono_reparto': _('Teléfono de reparto'),
            'direccion_local': _('Dirección local'),
            'ciudad': _('Ciudad'),
            'provincia': _('Provincia'),
            'codigo_postal': _('Código postal'),
            'tipo_entrega': _('Tipo de entrega'),
            'direccion_entrega': _('Dirección de entrega'),
            'ciudad_entrega': _('Ciudad de entrega'),
            'provincia_entrega': _('Provincia de entrega'),
            'codigo_postal_entrega': _('Código postal de entrega'),
        }
        
        errors = []
        for field, label in required_fields.items():
            value = getattr(user, field)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f'{label}')
        
        if errors:
            messages.error(request, _('Por favor completa los siguientes campos obligatorios: ') + ', '.join(errors))
        else:
            user.save()
            
            # Log action
            log_profile_action(
                user=user,
                action='update_complete_profile',
                field_changed='multiple',
                request=request
            )
            
            messages.success(request, _('Tu perfil ha sido actualizado correctamente'))
            return redirect('accounts:profile_dashboard')
    
    # Detectar campos faltantes
    required_fields_list = [
        'telefono_reparto',
        'direccion_local',
        'ciudad',
        'provincia',
        'codigo_postal',
        'tipo_entrega',
        'direccion_entrega',
        'ciudad_entrega',
        'provincia_entrega',
        'codigo_postal_entrega',
    ]
    
    missing_fields = []
    for field in required_fields_list:
        value = getattr(user, field, None)
        if not value or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)
    
    context = {
        'user': user,
        'edit_mode': True,
        'missing_fields': missing_fields,
    }
    
    return render(request, 'accounts/profile/profile_dashboard_new.html', context)


# ============================================================
# VISTAS DE ADMINISTRACIÓN: Ver/Editar perfiles de otros usuarios
# Solo para SUPER_ADMIN y ADMIN
# ============================================================

@login_required
def admin_view_user_profile(request, user_id):
    """
    Vista para que ADMIN/SUPER_ADMIN vea el perfil de otro usuario.
    
    RBAC: Solo SUPER_ADMIN y ADMIN pueden acceder.
    NUNCA usuarios normales.
    """
    # RBAC: Verificar permisos
    if not request.user.can_manage_users():
        messages.error(request, _('No tienes permisos para acceder a esta sección'))
        return redirect('accounts:dashboard')
    
    # Obtener usuario objetivo
    target_user = get_object_or_404(User, id=user_id)
    
    # RBAC: ADMIN no puede ver perfiles de SUPER_ADMIN
    if target_user.is_super_admin() and not request.user.is_super_admin():
        messages.error(request, _('No tienes permisos para ver este usuario'))
        return redirect('accounts:user_approval_dashboard')
    
    # Obtener preferencias y seguridad
    preferences = target_user.get_or_create_preferences()
    security = target_user.get_or_create_security()
    
    # Obtener organización
    user_company = UserCompany.objects.filter(user=target_user).first()
    
    # Sesiones activas
    active_sessions_count = UserSession.objects.filter(
        user=target_user,
        is_active=True,
        expires_at__gt=timezone.now()
    ).count()
    
    context = {
        'target_user': target_user,
        'preferences': preferences,
        'security': security,
        'user_company': user_company,
        'active_sessions_count': active_sessions_count,
        'view_mode': True,  # Solo lectura
        'is_admin_view': True,
    }
    
    return render(request, 'accounts/profile/admin_view_user.html', context)


@login_required
def admin_edit_user_profile(request, user_id):
    """
    Vista para que ADMIN/SUPER_ADMIN edite el perfil de otro usuario.
    
    RBAC: Solo SUPER_ADMIN y ADMIN pueden acceder.
    NUNCA usuarios normales.
    """
    # RBAC: Verificar permisos
    if not request.user.can_manage_users():
        messages.error(request, _('No tienes permisos para acceder a esta sección'))
        return redirect('accounts:dashboard')
    
    # Obtener usuario objetivo
    target_user = get_object_or_404(User, id=user_id)
    
    # RBAC: ADMIN no puede editar perfiles de SUPER_ADMIN
    if target_user.is_super_admin() and not request.user.is_super_admin():
        messages.error(request, _('No tienes permisos para editar este usuario'))
        return redirect('accounts:user_approval_dashboard')
    
    # Obtener tab activo
    active_tab = request.GET.get('tab', 'info-general')
    
    # Obtener preferencias y seguridad
    preferences = target_user.get_or_create_preferences()
    security = target_user.get_or_create_security()
    
    # Obtener organización
    user_company = UserCompany.objects.filter(user=target_user).first()
    
    context = {
        'target_user': target_user,
        'preferences': preferences,
        'security': security,
        'user_company': user_company,
        'active_tab': active_tab,
        'edit_mode': True,
        'is_admin_view': True,
    }
    
    return render(request, 'accounts/profile/admin_edit_user.html', context)