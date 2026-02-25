# 🔒 Sistema RBAC (Roles y Permisos)

Plataforma Fenix utiliza un sistema de Control de Acceso Basado en Roles (RBAC) para gestionar los permisos de los usuarios de forma jerárquica.

## Roles Oficiales
- 🟣 **SUPER_ADMIN**: Control total. Gestión de todos los usuarios y configuración global.
- 🔵 **ADMIN**: Backoffice operativo. Gestión de pedidos, productos y usuarios (excepto super_admins).
- 🟢 **USER**: Cliente final. Acceso al catálogo y a sus propios pedidos.

## Matriz de Permisos

| Funcionalidad | SUPER_ADMIN | ADMIN | USER |
|---------------|-------------|-------|------|
| Gestión de Usuarios | ✅ Todos | ✅ admin/user | ❌ |
| Ver super_admin | ✅ | ❌ | ❌ |
| Asignar super_admin | ✅ | ❌ | ❌ |
| Aprobar usuarios | ✅ | ✅ | ❌ |
| Configuración global | ✅ | ❌ | ❌ |
| Ver todos los pedidos | ✅ | ✅ | ❌ |
| Ver propios pedidos | ✅ | ✅ | ✅ |

## Implementación Técnica
- **Modelo de Usuario**: Campo `role` con opciones `super_admin`, `admin`, `user`.
- **Protección Backend**: Decoradores `@admin_required`, `@super_admin_required` y helpers en `accounts/permissions.py`.
- **Protección Frontend**: Menús condicionales en `sidebar.html` y filtros en templates.

## Reglas Críticas
1. **Protección de Super Admins**: Los usuarios con rol `admin` no pueden ver, editar ni eliminar a los `super_admin`.
2. **Registro Público**: Siempre asigna el rol `user` por defecto.
3. **Soft Delete**: La eliminación de usuarios simplemente cambia su estado a `disabled`.
