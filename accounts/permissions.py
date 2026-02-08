"""
Sistema de permisos basado en roles (RBAC) para Fenix.

Roles oficiales:
- super_admin: Control total de la plataforma
- admin: Backoffice operativo (antes 'manager')
- user: Cliente final (antes 'client')
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from functools import wraps


# Constantes de roles (sincronizadas con User model)
ROLE_SUPER_ADMIN = 'super_admin'
ROLE_ADMIN = 'admin'
ROLE_USER = 'user'


def is_super_admin(user):
    """Verifica si el usuario es Super Admin."""
    if not user or not user.is_authenticated:
        return False
    return user.role == ROLE_SUPER_ADMIN


def is_admin(user):
    """Verifica si el usuario es Admin (manager)."""
    if not user or not user.is_authenticated:
        return False
    return user.role == ROLE_ADMIN


def is_user(user):
    """Verifica si el usuario es User/Client."""
    if not user or not user.is_authenticated:
        return False
    return user.role == ROLE_USER


def can_manage_users(user):
    """
    Verifica si el usuario puede acceder a Gestión de Usuarios.
    Solo SUPER_ADMIN y ADMIN tienen acceso.
    """
    return is_super_admin(user) or is_admin(user)


def can_edit_target(editor, target_user):
    """
    Verifica si 'editor' puede editar 'target_user'.
    
    Reglas:
    - SUPER_ADMIN puede editar a cualquiera (incluidos otros super_admin)
    - ADMIN puede editar user y admin, pero NO super_admin
    - USER no puede editar a nadie (excepto su propio perfil)
    """
    if not editor or not editor.is_authenticated:
        return False
    
    if not target_user:
        return False
    
    # Un usuario siempre puede editar su propio perfil (con limitaciones)
    if editor.id == target_user.id:
        return True
    
    # SUPER_ADMIN puede editar a cualquiera
    if is_super_admin(editor):
        return True
    
    # ADMIN puede editar user y admin, pero NO super_admin
    if is_admin(editor):
        if is_super_admin(target_user):
            return False  # ADMIN no puede tocar SUPER_ADMIN
        return True  # Puede editar user y admin
    
    # USER no puede editar a otros
    return False


def can_assign_role(editor, target_role):
    """
    Verifica si 'editor' puede asignar 'target_role' a un usuario.
    
    Reglas:
    - SUPER_ADMIN puede asignar cualquier role
    - ADMIN puede asignar 'user' y 'admin', pero NO 'super_admin'
    - USER no puede asignar roles
    """
    if not editor or not editor.is_authenticated:
        return False
    
    # SUPER_ADMIN puede asignar cualquier role
    if is_super_admin(editor):
        return True
    
    # ADMIN puede asignar user y admin, pero NO super_admin
    if is_admin(editor):
        return target_role in [ROLE_USER, ROLE_ADMIN]
    
    # USER no puede asignar roles
    return False


def can_delete_target(editor, target_user):
    """
    Verifica si 'editor' puede eliminar 'target_user'.
    
    Reglas:
    - SUPER_ADMIN puede eliminar a cualquiera (excepto a sí mismo)
    - ADMIN puede eliminar user y admin, pero NO super_admin
    - USER no puede eliminar a nadie
    """
    if not editor or not editor.is_authenticated:
        return False
    
    if not target_user:
        return False
    
    # Nadie puede eliminarse a sí mismo
    if editor.id == target_user.id:
        return False
    
    # SUPER_ADMIN puede eliminar a cualquiera
    if is_super_admin(editor):
        return True
    
    # ADMIN puede eliminar user y admin, pero NO super_admin
    if is_admin(editor):
        if is_super_admin(target_user):
            return False
        return True
    
    # USER no puede eliminar a nadie
    return False


def get_role_choices_for_user(user):
    """
    Retorna las opciones de roles que 'user' puede asignar.
    
    - SUPER_ADMIN ve: super_admin, admin, user
    - ADMIN ve: admin, user (NO super_admin)
    - USER ve: [] (no puede asignar roles)
    """
    from accounts.models import User
    
    if not user or not user.is_authenticated:
        return []
    
    if is_super_admin(user):
        return User.ROLE_CHOICES
    
    if is_admin(user):
        # ADMIN no puede asignar super_admin
        return [
            (ROLE_ADMIN, 'Admin'),
            (ROLE_USER, 'User'),
        ]
    
    return []


def get_visible_users_queryset(user, base_queryset):
    """
    Filtra el queryset de usuarios según el rol del usuario logado.
    
    - SUPER_ADMIN ve todos los usuarios
    - ADMIN ve todos EXCEPTO super_admin
    - USER solo se ve a sí mismo
    """
    if not user or not user.is_authenticated:
        return base_queryset.none()
    
    # SUPER_ADMIN ve todos
    if is_super_admin(user):
        return base_queryset
    
    # ADMIN ve todos excepto super_admin
    if is_admin(user):
        return base_queryset.exclude(role=ROLE_SUPER_ADMIN)
    
    # USER solo se ve a sí mismo
    return base_queryset.filter(id=user.id)


# =============================================================================
# DECORADORES DE PERMISOS
# =============================================================================

def super_admin_required(view_func):
    """
    Decorador que requiere que el usuario sea SUPER_ADMIN.
    Redirige a 403 si no tiene permisos.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_super_admin(request.user):
            messages.error(request, _('No tienes permisos para acceder a esta sección.'))
            return redirect('catalog:product_list')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """
    Decorador que requiere que el usuario sea ADMIN o SUPER_ADMIN.
    Redirige a 403 si no tiene permisos.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not can_manage_users(request.user):
            messages.error(request, _('No tienes permisos para acceder a esta sección.'))
            return redirect('catalog:product_list')
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_required(view_func):
    """
    Decorador que requiere que el usuario sea ADMIN o SUPER_ADMIN.
    Alias de admin_required para mayor claridad.
    """
    return admin_required(view_func)
