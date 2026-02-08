"""
Script de prueba para validar las reglas RBAC del sistema.

Ejecutar: python test_rbac.py

Este script valida:
1. Helpers de permisos funcionan correctamente
2. Visibilidad de usuarios según rol
3. Permisos de edición/eliminación
4. Asignación de roles
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fenix.settings')
django.setup()

from accounts.models import User
from accounts.permissions import (
    is_super_admin,
    is_admin,
    is_user,
    can_manage_users,
    can_edit_target,
    can_assign_role,
    can_delete_target,
    get_visible_users_queryset,
    get_role_choices_for_user,
    ROLE_SUPER_ADMIN,
    ROLE_ADMIN,
    ROLE_USER
)


def test_helpers():
    """Prueba los helpers de identificación de roles"""
    print("\n" + "="*70)
    print("TEST 1: HELPERS DE ROLES")
    print("="*70)
    
    # Buscar o crear usuarios de prueba
    super_admin = User.objects.filter(role=ROLE_SUPER_ADMIN).first()
    admin = User.objects.filter(role=ROLE_ADMIN).first()
    user = User.objects.filter(role=ROLE_USER).first()
    
    print(f"\n✅ Super Admin encontrado: {super_admin.email if super_admin else 'N/A'}")
    print(f"   - is_super_admin(): {is_super_admin(super_admin) if super_admin else 'N/A'}")
    print(f"   - can_manage_users(): {can_manage_users(super_admin) if super_admin else 'N/A'}")
    
    print(f"\n✅ Admin encontrado: {admin.email if admin else 'N/A'}")
    print(f"   - is_admin(): {is_admin(admin) if admin else 'N/A'}")
    print(f"   - can_manage_users(): {can_manage_users(admin) if admin else 'N/A'}")
    
    print(f"\n✅ User encontrado: {user.email if user else 'N/A'}")
    print(f"   - is_user(): {is_user(user) if user else 'N/A'}")
    print(f"   - can_manage_users(): {can_manage_users(user) if user else 'N/A'}")


def test_visibility():
    """Prueba la visibilidad de usuarios según rol"""
    print("\n" + "="*70)
    print("TEST 2: VISIBILIDAD DE USUARIOS")
    print("="*70)
    
    all_users = User.objects.all()
    super_admin = User.objects.filter(role=ROLE_SUPER_ADMIN).first()
    admin = User.objects.filter(role=ROLE_ADMIN).first()
    user = User.objects.filter(role=ROLE_USER).first()
    
    print(f"\nTotal de usuarios en BD: {all_users.count()}")
    print(f"  - Super Admins: {all_users.filter(role=ROLE_SUPER_ADMIN).count()}")
    print(f"  - Admins: {all_users.filter(role=ROLE_ADMIN).count()}")
    print(f"  - Users: {all_users.filter(role=ROLE_USER).count()}")
    
    if super_admin:
        visible = get_visible_users_queryset(super_admin, all_users)
        print(f"\n✅ SUPER_ADMIN ve: {visible.count()} usuarios (todos)")
    
    if admin:
        visible = get_visible_users_queryset(admin, all_users)
        print(f"✅ ADMIN ve: {visible.count()} usuarios (sin super_admin)")
        super_admin_visible = visible.filter(role=ROLE_SUPER_ADMIN).exists()
        print(f"   ⚠️  SUPER_ADMIN visible para ADMIN: {super_admin_visible} (debe ser False)")
    
    if user:
        visible = get_visible_users_queryset(user, all_users)
        print(f"✅ USER ve: {visible.count()} usuario(s) (solo sí mismo)")


def test_edit_permissions():
    """Prueba permisos de edición"""
    print("\n" + "="*70)
    print("TEST 3: PERMISOS DE EDICIÓN")
    print("="*70)
    
    super_admin = User.objects.filter(role=ROLE_SUPER_ADMIN).first()
    admin = User.objects.filter(role=ROLE_ADMIN).first()
    user = User.objects.filter(role=ROLE_USER).first()
    
    if super_admin and admin:
        print(f"\n✅ SUPER_ADMIN puede editar ADMIN: {can_edit_target(super_admin, admin)}")
        print(f"✅ ADMIN puede editar SUPER_ADMIN: {can_edit_target(admin, super_admin)} (debe ser False)")
    
    if admin and user:
        print(f"✅ ADMIN puede editar USER: {can_edit_target(admin, user)}")
    
    if user and admin:
        print(f"✅ USER puede editar ADMIN: {can_edit_target(user, admin)} (debe ser False)")


def test_delete_permissions():
    """Prueba permisos de eliminación"""
    print("\n" + "="*70)
    print("TEST 4: PERMISOS DE ELIMINACIÓN")
    print("="*70)
    
    super_admin = User.objects.filter(role=ROLE_SUPER_ADMIN).first()
    admin = User.objects.filter(role=ROLE_ADMIN).first()
    user = User.objects.filter(role=ROLE_USER).first()
    
    if super_admin and admin:
        print(f"\n✅ SUPER_ADMIN puede eliminar ADMIN: {can_delete_target(super_admin, admin)}")
        print(f"✅ SUPER_ADMIN puede eliminarse a sí mismo: {can_delete_target(super_admin, super_admin)} (debe ser False)")
        print(f"✅ ADMIN puede eliminar SUPER_ADMIN: {can_delete_target(admin, super_admin)} (debe ser False)")
    
    if admin and user:
        print(f"✅ ADMIN puede eliminar USER: {can_delete_target(admin, user)}")


def test_role_assignment():
    """Prueba asignación de roles"""
    print("\n" + "="*70)
    print("TEST 5: ASIGNACIÓN DE ROLES")
    print("="*70)
    
    super_admin = User.objects.filter(role=ROLE_SUPER_ADMIN).first()
    admin = User.objects.filter(role=ROLE_ADMIN).first()
    user = User.objects.filter(role=ROLE_USER).first()
    
    if super_admin:
        print(f"\n✅ SUPER_ADMIN puede asignar 'super_admin': {can_assign_role(super_admin, ROLE_SUPER_ADMIN)}")
        print(f"✅ SUPER_ADMIN puede asignar 'admin': {can_assign_role(super_admin, ROLE_ADMIN)}")
        print(f"✅ SUPER_ADMIN puede asignar 'user': {can_assign_role(super_admin, ROLE_USER)}")
    
    if admin:
        print(f"\n✅ ADMIN puede asignar 'super_admin': {can_assign_role(admin, ROLE_SUPER_ADMIN)} (debe ser False)")
        print(f"✅ ADMIN puede asignar 'admin': {can_assign_role(admin, ROLE_ADMIN)}")
        print(f"✅ ADMIN puede asignar 'user': {can_assign_role(admin, ROLE_USER)}")
    
    if user:
        print(f"\n✅ USER puede asignar roles: {can_assign_role(user, ROLE_USER)} (debe ser False)")


def test_role_choices():
    """Prueba opciones de roles disponibles"""
    print("\n" + "="*70)
    print("TEST 6: OPCIONES DE ROLES DISPONIBLES")
    print("="*70)
    
    super_admin = User.objects.filter(role=ROLE_SUPER_ADMIN).first()
    admin = User.objects.filter(role=ROLE_ADMIN).first()
    user = User.objects.filter(role=ROLE_USER).first()
    
    if super_admin:
        choices = get_role_choices_for_user(super_admin)
        print(f"\n✅ SUPER_ADMIN ve {len(choices)} opciones: {[c[0] for c in choices]}")
    
    if admin:
        choices = get_role_choices_for_user(admin)
        print(f"✅ ADMIN ve {len(choices)} opciones: {[c[0] for c in choices]}")
        has_super_admin = any(c[0] == ROLE_SUPER_ADMIN for c in choices)
        print(f"   ⚠️  Incluye 'super_admin': {has_super_admin} (debe ser False)")
    
    if user:
        choices = get_role_choices_for_user(user)
        print(f"✅ USER ve {len(choices)} opciones: {[c[0] for c in choices]} (debe ser vacío)")


def main():
    print("\n" + "🔒 " + "="*66 + " 🔒")
    print("   PRUEBA DE SISTEMA RBAC - FENIX")
    print("🔒 " + "="*66 + " 🔒")
    
    try:
        test_helpers()
        test_visibility()
        test_edit_permissions()
        test_delete_permissions()
        test_role_assignment()
        test_role_choices()
        
        print("\n" + "="*70)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
