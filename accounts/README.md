# Accounts App

Esta aplicación gestiona el modelo de usuario, la autenticación y el sistema de permisos (RBAC) de la plataforma.

## Modelos Principales
- **User**: Modelo personalizado que extiende `AbstractUser`. Incluye campos para:
    - `role`: (super_admin, admin, user)
    - `status`: (pending, active, rejected, disabled)
    - `email_verified`: Boolean para el primer paso de seguridad.
    - `company`: Datos de la empresa asociada.

## Seguridad y Permisos
- **Middleware**: `UserApprovalMiddleware` asegura que solo usuarios verificados y activos accedan a rutas protegidas.
- **Permissions**: Helpers en `permissions.py` para lógica RBAC (ej. `is_admin`, `can_edit_target`).

## Vistas Clave
- `login_view`, `register_view`: Gestión de acceso con validación de "2 pasos".
- `profile_dashboard`: Gestión completa del perfil del usuario (seguridad, 2FA, sesiones).
- `user_approval_list`: Panel para que admins aprueben nuevos registros.
