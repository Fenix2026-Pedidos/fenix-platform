# Sistema de Autenticación Completo - Fenix Platform

## 📋 Índice
1. [Introducción](#introducción)
2. [Estados de Usuario](#estados-de-usuario)
3. [Flujo de Registro](#flujo-de-registro)
4. [Flujo de Login](#flujo-de-login)
5. [Verificación de Email](#verificación-de-email)
6. [Restablecimiento de Contraseña](#restablecimiento-de-contraseña)
7. [Administración de Usuarios](#administración-de-usuarios)
8. [Configuración](#configuración)

---

## Introducción

Este sistema implementa un flujo completo de autenticación con múltiples estados de usuario, verificación de email y aprobación administrativa.

### Características Principales
- ✅ Autenticación basada en email
- ✅ Verificación de email con tokens de 24 horas
- ✅ Sistema de aprobación de usuarios (Manager/Admin)
- ✅ Restablecimiento de contraseña integrado
- ✅ Reenvío de email de confirmación
- ✅ UI moderna con Bootstrap Icons
- ✅ Soporte multiidioma (es, zh-hans)

---

## Estados de Usuario

Un usuario en Fenix puede tener los siguientes estados:

### 1. **Email No Verificado** (`email_verified = False`)
- Usuario recién registrado
- No puede iniciar sesión
- Debe verificar su email primero
- Recibe email con token de verificación

### 2. **Email Verificado, Pendiente de Aprobación** (`email_verified = True, pending_approval = True`)
- Usuario verificó su email
- No puede iniciar sesión (excepto Admin/Manager)
- Espera aprobación de un Manager o Super Admin
- Ve mensaje informativo

### 3. **Aprobado y Activo** (`email_verified = True, pending_approval = False, is_active = True`)
- Usuario completamente operativo
- Puede iniciar sesión normalmente
- Acceso completo según su rol

### 4. **Desactivado** (`is_active = False`)
- Cuenta bloqueada/suspendida
- No puede iniciar sesión
- Requiere reactivación por Admin

### Roles Disponibles
- **super_admin**: Acceso total al sistema
- **manager**: Gestión de productos, pedidos y aprobación de usuarios
- **client**: Usuario final con acceso a catálogo y pedidos

---

## Flujo de Registro

### 1. Usuario accede a `/accounts/register/`
```
Campos requeridos:
- Email (único)
- Nombre completo
- Contraseña (8+ caracteres)
- Confirmar contraseña
- Idioma preferido (es/zh-hans)
```

### 2. Al enviar el formulario:
```python
# El sistema crea el usuario con:
email_verified = False
pending_approval = True
is_active = True
```

### 3. Se genera un token de verificación:
```python
EmailVerificationToken(
    user=user,
    token=UUID,
    expires_at=now + 24 horas
)
```

### 4. Se envía email con enlace de verificación:
```
Asunto: "FENIX - Verifica tu email"
Enlace: /accounts/verify-email/?token={UUID}
Expiración: 24 horas
```

### 5. Usuario ve mensaje:
```
"Registro exitoso. Por favor verifica tu email para continuar."
```

---

## Flujo de Login

### 1. Usuario ingresa email y contraseña en `/accounts/login/`

### 2. Validaciones en orden:

#### A. Credenciales incorrectas
```
❌ "Credenciales inválidas"
→ Permanece en página de login
```

#### B. Cuenta desactivada (`is_active = False`)
```
❌ "Tu cuenta está desactivada"
→ Permanece en página de login
```

#### C. Email no verificado (`email_verified = False`)
```
⚠️ "Debes verificar tu email antes de iniciar sesión"
→ Redirige a /accounts/email-verification/
→ Muestra botón "Reenviar Email"
```

#### D. Pendiente de aprobación (`pending_approval = True`)
```
ℹ️ "Tu cuenta está pendiente de aprobación por un administrador"
→ Redirige a /accounts/pending-approval/
→ Muestra información del estado

EXCEPCIÓN: Usuarios con rol 'manager' o 'super_admin' pueden entrar
```

#### E. Todo OK
```
✅ "Bienvenido, [Nombre]!"
→ Redirige a catálogo o URL especificada en ?next=
```

### 3. Características UI:
- 🔒 Toggle para mostrar/ocultar contraseña
- 🔑 Enlace "¿Olvidaste tu contraseña?"
- 📧 Iconos para email y contraseña
- 📱 Diseño responsive

---

## Verificación de Email

### Vista: `/accounts/verify-email/?token={UUID}`

### Proceso:
```python
1. Se busca el token en la base de datos
2. Validaciones:
   - Token existe ✓
   - No ha expirado (< 24 horas) ✓
   - No ha sido usado (is_used = False) ✓

3. Si es válido:
   - user.email_verified = True
   - token.is_used = True
   - Mensaje: "¡Email verificado exitosamente!"
   - Redirige a login

4. Si es inválido:
   - Mensaje: "Este enlace ha expirado o ya fue usado"
   - Redirige a login
```

### Reenvío de Email (`/accounts/resend-confirmation/`)

**Endpoint:** POST `/accounts/resend-confirmation/`

**Request:**
```json
{
  "email": "usuario@ejemplo.com"
}
```

**Validaciones:**
1. Email existe ✓
2. Email no está ya verificado ✓
3. No se envió otro email en los últimos 5 minutos ✓

**Response exitosa:**
```json
{
  "success": true,
  "message": "Email de confirmación enviado."
}
```

**Response de error:**
```json
{
  "success": false,
  "error": "Ya se envió un email recientemente. Por favor espera unos minutos."
}
```

### Página de Verificación Pendiente

**Vista:** `/accounts/email-verification/`

**Elementos UI:**
- 📧 Icono de email grande
- 📝 Email del usuario
- 🔄 Botón "Reenviar Email de Verificación"
- ⏱️ Mensaje: "El enlace expira en 24 horas"
- 🔙 Link de regreso al login

---

## Restablecimiento de Contraseña

### Flujo Completo

#### 1. Solicitar Restablecimiento
**URL:** `/accounts/password-reset/`

**Template:** `password_reset_form.html`

```
Usuario ingresa su email
↓
Django envía email con enlace único
↓
Redirige a: /accounts/password-reset/done/
```

#### 2. Email Enviado
**URL:** `/accounts/password-reset/done/`

**Template:** `password_reset_done.html`

```
✅ "Email enviado"
💡 "Revisa tu bandeja de entrada y spam"
```

#### 3. Confirmar Nueva Contraseña
**URL:** `/accounts/password-reset-confirm/<uidb64>/<token>/`

**Template:** `password_reset_confirm.html`

**Validaciones:**
- Enlace válido y no expirado
- Contraseñas coinciden
- Mínimo 8 caracteres
- No completamente numérica

**Características UI:**
- 👁️ Toggle para mostrar/ocultar contraseñas
- 🔒 Iconos para cada campo
- 💡 Tooltip con requisitos
- ✅ Validación visual

#### 4. Contraseña Cambiada
**URL:** `/accounts/password-reset-complete/`

**Template:** `password_reset_complete.html`

```
✅ "¡Contraseña cambiada!"
🔐 "Ya puedes iniciar sesión con tu nueva contraseña"
→ Botón: "Iniciar Sesión"
```

### Emails de Restablecimiento

**Asunto:** `password_reset_subject.txt`
```
FENIX - Restablecer Contraseña
```

**Cuerpo:** `password_reset_email.html`
```
Hola,

Has solicitado restablecer tu contraseña para tu cuenta en FENIX.

Por favor haz clic en el siguiente enlace:
[Enlace único y seguro]

Si no solicitaste este cambio, ignora este email.

Este enlace expirará en unas horas.

Saludos,
El equipo de FENIX
```

---

## Administración de Usuarios

### Panel de Aprobación (Manager/Admin)

**URL:** `/accounts/approval/`

**Permisos:** Solo `manager` y `super_admin`

**Funcionalidad:**
```python
1. Lista usuarios con:
   - pending_approval = True
   - is_active = True
   
2. Muestra por usuario:
   - Email
   - Nombre completo
   - Rol solicitado
   - Fecha de registro
   - Estado de verificación de email
   - Botón "Aprobar"
   
3. Al aprobar:
   - pending_approval = False
   - Se envía email de notificación
   - Se registra en AuditLog
```

### Aprobar Usuario

**URL:** `/accounts/approve/<user_id>/`

**Método:** POST

**Proceso:**
```python
1. Verificar permisos (manager/super_admin)
2. Obtener usuario
3. Validar que esté pendiente
4. Cambiar estado:
   user.pending_approval = False
   user.save()
5. Enviar email de notificación
6. Crear AuditLog:
   - action = 'user_approved'
   - target = user.email
   - performed_by = request.user
7. Mensaje: "Usuario aprobado exitosamente"
```

### Django Admin

**Modelo User:**
```python
Campos visibles:
- email, full_name, role, language
- is_active, is_staff
- email_verified, pending_approval
- date_joined

Filtros:
- role, language, is_active, is_staff

Búsqueda:
- email, full_name
```

**Modelo EmailVerificationToken:**
```python
Campos visibles:
- user, token, created_at, expires_at, is_used

Filtros:
- is_used, created_at

Búsqueda:
- user__email, token

Readonly:
- token, created_at, expires_at
```

---

## Configuración

### URLs

**accounts/urls.py:**
```python
# Autenticación básica
/accounts/login/              → login_view
/accounts/logout/             → logout_view
/accounts/register/           → register_view
/accounts/profile/            → profile_view

# Verificación de email
/accounts/email-verification/ → email_verification_view
/accounts/verify-email/       → verify_email (token en query)
/accounts/resend-confirmation/ → resend_confirmation (POST)

# Aprobación de usuarios
/accounts/pending-approval/   → pending_approval_view
/accounts/approval/           → user_approval_list
/accounts/approve/<id>/       → user_approve

# Restablecimiento de contraseña
/accounts/password-reset/                  → PasswordResetView
/accounts/password-reset/done/             → PasswordResetDoneView
/accounts/password-reset-confirm/<uidb64>/<token>/ → PasswordResetConfirmView
/accounts/password-reset-complete/         → PasswordResetCompleteView
```

### Modelos

**User:**
```python
email: EmailField (unique, USERNAME_FIELD)
full_name: CharField(200)
role: CharField (super_admin, manager, client)
language: CharField (es, zh-hans)
email_verified: BooleanField (default=False)
pending_approval: BooleanField (default=True)
is_active: BooleanField (default=True)
is_staff: BooleanField (default=False)
date_joined: DateTimeField (auto_now_add)
```

**EmailVerificationToken:**
```python
user: ForeignKey(User) → related_name='verification_tokens'
token: UUIDField (unique, auto-generated)
created_at: DateTimeField (auto_now_add)
expires_at: DateTimeField (created + 24 horas)
is_used: BooleanField (default=False)

Métodos:
- is_valid(): Retorna si token no usado y no expirado
```

### Email Backend

**Desarrollo (settings.py):**
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@fenix.com'
```
→ Los emails se muestran en la consola

**Producción:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@fenix.com'
```

### Variables de Sesión

```python
# Login view guarda email si no verificado:
request.session['unverified_user_email'] = user.email

# Email verification view usa:
email = request.session.get('unverified_user_email', '')
```

---

## Testing del Sistema

### 1. Registro de Usuario
```bash
1. Acceder a http://127.0.0.1:8000/accounts/register/
2. Llenar formulario
3. Verificar redirección a login
4. Verificar email en consola del servidor
5. Copiar token del enlace
```

### 2. Verificación de Email
```bash
1. Acceder a /accounts/verify-email/?token={UUID}
2. Verificar mensaje de éxito
3. Verificar en admin: user.email_verified = True
4. Verificar en admin: token.is_used = True
```

### 3. Login Sin Aprobación
```bash
1. Intentar login
2. Verificar redirección a /accounts/pending-approval/
3. Ver mensaje informativo
```

### 4. Aprobación de Usuario
```bash
1. Login como super_admin
2. Acceder a /accounts/approval/
3. Ver usuario pendiente
4. Hacer clic en "Aprobar"
5. Verificar email de notificación en consola
```

### 5. Login Exitoso
```bash
1. Logout del admin
2. Login con usuario aprobado
3. Verificar acceso al sistema
4. Verificar redirección a catálogo
```

### 6. Restablecimiento de Contraseña
```bash
1. En login, clic en "¿Olvidaste tu contraseña?"
2. Ingresar email
3. Verificar email en consola
4. Copiar enlace
5. Ingresar nueva contraseña
6. Verificar login con nueva contraseña
```

### 7. Reenvío de Confirmación
```bash
1. En /accounts/email-verification/
2. Hacer clic en "Reenviar Email"
3. Verificar respuesta AJAX
4. Verificar nuevo email en consola
5. Verificar rate limit (no permitir < 5 min)
```

---

## Solución de Problemas

### Email no se envía
```
Causa: EMAIL_BACKEND mal configurado
Solución: Verificar settings.py
```

### Token expirado
```
Causa: Token > 24 horas
Solución: Solicitar reenvío de email
```

### Usuario no puede entrar después de aprobar
```
Causa: email_verified = False
Solución: 
1. Verificar que completó verificación de email
2. En admin, cambiar manualmente email_verified = True
```

### Administrador no puede aprobar usuarios
```
Causa: Usuario no tiene rol manager o super_admin
Solución: En admin, cambiar role del usuario
```

### Error CSRF
```
Causa: Token CSRF falta o inválido
Solución: Verificar {% csrf_token %} en formularios
```

---

## Seguridad

### Medidas Implementadas

1. **Tokens únicos UUID4**
   - No predecibles
   - Alta entropía

2. **Expiración de tokens**
   - 24 horas para verificación de email
   - Configurado por Django para password reset

3. **Rate limiting**
   - Reenvío de email: máximo 1 cada 5 minutos
   - Previene spam

4. **Validación de tokens**
   - Verificar existencia
   - Verificar expiración
   - Verificar uso único
   - Marcar como usado después de usar

5. **CSRF Protection**
   - Todos los formularios con {% csrf_token %}
   - APIs POST con validación CSRF

6. **Password requirements**
   - Mínimo 8 caracteres
   - No completamente numérica
   - Validaciones de Django incorporadas

7. **Email verification required**
   - No login sin email verificado
   - Previene cuentas falsas

8. **Admin approval**
   - Control de acceso adicional
   - Previene registros maliciosos

---

## Próximas Mejoras

- [ ] OAuth (Google, GitHub)
- [ ] 2FA (Two-Factor Authentication)
- [ ] Sesiones múltiples
- [ ] Historial de logins
- [ ] Bloqueo de cuenta después de X intentos fallidos
- [ ] Notificaciones push
- [ ] API REST para autenticación
- [ ] Confirmación de cambio de email
- [ ] Soft delete de usuarios

---

## Changelog

### v1.0.0 (03/02/2026)
- ✅ Sistema completo de autenticación
- ✅ Verificación de email con tokens
- ✅ Sistema de aprobación de usuarios
- ✅ Restablecimiento de contraseña
- ✅ Templates modernos con UI mejorada
- ✅ Reenvío de emails de confirmación
- ✅ Rate limiting en reenvío
- ✅ Administración completa en Django Admin
- ✅ Soporte multiidioma (es, zh-hans)
- ✅ Documentación completa

---

## Autor
Fenix Development Team - 2026
