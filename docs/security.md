# 🔐 Sistema de Seguridad de 2 Pasos

Este documento describe la arquitectura y el funcionamiento del sistema de seguridad de 2 pasos implementado en Plataforma Fenix.

## Descripción General
Se ha implementado un sistema de autenticación que requiere dos puertas de verificación obligatorias:
1. **Verificación de Email** ✉️: El usuario confirma la propiedad de su dirección de correo.
2. **Aprobación de Administrador** 👨‍💼: Un administrador valida manualmente la cuenta.

## Arquitectura de Seguridad (3 Capas)
El sistema utiliza una estrategia de "defensa en profundidad":

1. **Capa de Vista (Login)**: Verifica las puertas antes de crear la sesión.
2. **Capa de Middleware**: Verifica las condiciones en cada solicitud a rutas protegidas.
3. **Capa de Base de Datos**: Mantiene el estado de `email_verified` y `status`.

## Flujo Técnico
### 1. Registro
- El usuario se registra y se crea con `email_verified=False` y `status='pending'`.
- Se envía un correo de verificación.

### 2. Verificación de Email
- Al hacer clic en el enlace, `email_verified` se marca como `True`.
- El usuario es redirigido a una página de "Pendiente de Aprobación".

### 3. Aprobación Admin
- Un administrador cambia el `status` a `active` desde el panel de gestión.
- El sistema registra `approved_by` y `approved_at`.
- Se envía un correo de confirmación al usuario.

## Configuración y Middleware
El middleware `accounts.middleware.UserApprovalMiddleware` es el encargado de forzar estas reglas. 
Las rutas públicas como `/login/`, `/register/`, y `/verify-email/` están en una whitelist.

## Troubleshooting
- **Usuario no puede entrar**: Verificar en el shell `u.email_verified` (bool) y `u.status` ('pending', 'active', 'rejected', 'disabled').
- **Emails no llegan**: Verificar configuración SMTP en `settings.py` y logs del servidor.
