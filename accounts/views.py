from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import User
from .forms import LoginForm, RegisterForm
from .utils import send_verification_email, send_approval_notification, is_manager_or_admin


def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('catalog:product_list')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Verificar si es admin (pueden entrar aunque tengan pending_approval)
            is_admin = is_manager_or_admin(user)
            
            if not user.is_active:
                messages.error(request, _('Tu cuenta está desactivada.'))
            elif user.pending_approval and not is_admin:
                messages.warning(request, _('Tu cuenta está pendiente de aprobación por un administrador.'))
            else:
                login(request, user)
                messages.success(request, _('Bienvenido, %(name)s!') % {'name': user.full_name})
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('catalog:product_list')
    else:
        form = LoginForm(request)
    
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """Vista de registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('catalog:product_list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.pending_approval = True  # Requiere aprobación del manager
            user.email_verified = False
            user.is_active = True  # Activo pero pendiente de aprobación
            user.save()
            
            # Enviar email de verificación (informa sobre aprobación pendiente)
            try:
                send_verification_email(user)
            except Exception:
                pass  # No fallar el registro si el email falla
            
            messages.success(
                request,
                _('Registro exitoso. Tu cuenta está pendiente de aprobación por un administrador.')
            )
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


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
def user_approval_list(request):
    """
    Vista para Managers y Super Admin: lista de usuarios pendientes de aprobación.
    """
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para acceder a esta página.'))
        return redirect('catalog:product_list')
    
    # Obtener usuarios pendientes de aprobación
    pending_users = User.objects.filter(
        pending_approval=True,
        is_active=True
    ).order_by('-date_joined')
    
    context = {
        'pending_users': pending_users,
    }
    return render(request, 'accounts/user_approval_list.html', context)


@login_required
def user_approve(request, user_id):
    """
    Vista para aprobar un usuario (Manager/Super Admin).
    """
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para realizar esta acción.'))
        return redirect('catalog:product_list')
    
    user_to_approve = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            user_to_approve.pending_approval = False
            user_to_approve.email_verified = True  # Consideramos verificado al aprobar
            user_to_approve.save()
            
            # Enviar notificación
            try:
                send_approval_notification(user_to_approve, approved=True)
            except Exception:
                pass
            
            messages.success(
                request,
                _('Usuario %(email)s aprobado exitosamente.') % {'email': user_to_approve.email}
            )
        elif action == 'reject':
            user_to_approve.is_active = False
            user_to_approve.save()
            
            # Enviar notificación
            try:
                send_approval_notification(user_to_approve, approved=False)
            except Exception:
                pass
            
            messages.success(
                request,
                _('Solicitud de %(email)s rechazada.') % {'email': user_to_approve.email}
            )
        
        return redirect('accounts:user_approval_list')
    
    context = {
        'user_to_approve': user_to_approve,
    }
    return render(request, 'accounts/user_approve.html', context)
