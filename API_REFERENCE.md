# 🔌 REFERENCIA DE API - ENDPOINTS DE AUTENTICACIÓN

## Para Desarrolladores Integrando Fenix

Guía completa de endpoints para integración con el sistema de autenticación y aprobación de Fenix.

---

## 📡 BASE DE INFORMACIÓN

### URL Base

```
Development:  http://127.0.0.1:8000/
Production:   https://api.plataformafenix.com/
```

### Protocolo

- **Formato**: JSON
- **Seguridad**: HTTPS (CSRF protection en desarrollo)
- **Autenticación**: Session-based + Token (Custom)

---

## 🔐 AUTENTICACIÓN

### Session vs Token

Fenix soporta dos métodos:

1. **Session-based** (para web)
   - Cookies automáticas
   - CSRF protection
   - Ideal para SPAs

2. **Token-based** (para mobile/APIs)
   - Token en header
   - Sin CSRF
   - Ideal para apps nativas

---

## 📋 ENDPOINTS PÚBLICOS

### 1. Registro de Usuario (POST)

```http
POST /accounts/register/
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password1": "SecurePass123!",
  "password2": "SecurePass123!",
  "first_name": "Juan",
  "last_name": "Pérez"
}
```

**Respuesta Exitosa (200)**
```json
{
  "status": "success",
  "message": "Usuario registrado exitosamente",
  "user_id": 42,
  "email": "newuser@example.com",
  "next_step": "Verifica tu email"
}
```

**Respuesta Error (400)**
```json
{
  "status": "error",
  "errors": {
    "email": ["Email ya está registrado"],
    "password1": ["Password muy débil"]
  }
}
```

### Validaciones

- **Email**: Debe ser válido y único
- **Password**: Mínimo 8 caracteres, mezcla de mayús/minús/números
- **Nombres**: No pueden estar vacíos

---

### 2. Verificación de Email (GET/POST)

#### Método 1: Link del Email (GET)

Usuario recibe email con link:
```
http://127.0.0.1:8000/accounts/verify-email/?token=abc123xyz
```

Cuando hace clic:
- ✅ Email se marca como verificado
- 🔄 Usuario redirige a `/accounts/pending-approval/`
- ❌ No inicia sesión automáticamente (seguridad)

#### Método 2: Via API (POST)

```http
POST /accounts/verify-email/
Content-Type: application/json

{
  "token": "abc123xyz"
}
```

**Respuesta (200)**
```json
{
  "status": "success",
  "message": "Email verificado correctamente",
  "next_step": "Espera aprobación del admin"
}
```

**Respuesta Error (400)**
```json
{
  "status": "error",
  "message": "Token inválido o expirado",
  "suggestion": "Solicita nuevo email de verificación"
}
```

### Reenviar Email de Verificación (POST)

```http
POST /accounts/resend-verification-email/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Respuesta (200)**
```json
{
  "status": "success",
  "message": "Email enviado a user@example.com"
}
```

---

### 3. Login (POST)

```http
POST /accounts/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Valores Válidos:**
```json
{
  "status": "success",
  "user_id": 1,
  "email": "user@example.com",
  "first_name": "Juan",
  "message": "Login exitoso"
}
```

**Respuesta: Email no verificado (403)**
```json
{
  "status": "error",
  "error_code": "EMAIL_NOT_VERIFIED",
  "message": "Por favor verifica tu email",
  "redirect": "/accounts/email-verification/"
}
```

**Respuesta: Pendiente aprobación (403)**
```json
{
  "status": "error",
  "error_code": "PENDING_APPROVAL",
  "message": "Tu cuenta está pendiente de aprobación",
  "redirect": "/accounts/pending-approval/"
}
```

**Respuesta: Cuenta rechazada (403)**
```json
{
  "status": "error",
  "error_code": "REJECTED",
  "message": "Tu solicitud fue rechazada",
  "contact": "soporte@fenix.com"
}
```

**Respuesta: Cuenta deshabilitada (403)**
```json
{
  "status": "error",
  "error_code": "DISABLED",
  "message": "Tu cuenta está deshabilitada",
  "contact": "soporte@fenix.com"
}
```

**Credenciales inválidas (401)**
```json
{
  "status": "error",
  "message": "Email o password incorrecto"
}
```

---

### 4. Logout (POST/GET)

```http
POST /accounts/logout/
X-CSRFToken: [token]
```

**Respuesta (200)**
```json
{
  "status": "success",
  "message": "Sesión cerrada"
}
```

---

### 5. Estado de Aprobación Pendiente (GET)

```http
GET /accounts/pending-approval/
```

**Respuesta (200)**
```json
{
  "status": "pending",
  "email": "user@example.com",
  "message": "Tu cuenta está pendiente de aprobación del administrador",
  "average_review_time": "24-48 horas",
  "support_email": "soporte@fenix.com"
}
```

---

## 🔑 ENDPOINTS PROTEGIDOS

Requieren autenticación (usuario logged in + status=ACTIVE)

### 1. Perfil de Usuario (GET)

```http
GET /accounts/profile/
Authorization: Bearer [token]
```

**Respuesta (200)**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "status": "active",
  "email_verified": true,
  "created_at": "2026-02-19T10:30:00Z",
  "approved_at": "2026-02-19T14:00:00Z",
  "approved_by": "admin@fenix.com"
}
```

**Respuesta Error: No autenticado (401)**
```json
{
  "status": "error",
  "message": "Debes estar logueado"
}
```

---

### 2. Actualizar Perfil (PATCH/PUT)

```http
PATCH /accounts/profile/
Authorization: Bearer [token]
Content-Type: application/json

{
  "first_name": "Juan Carlos",
  "last_name": "Pérez García"
}
```

**Respuesta (200)**
```json
{
  "status": "success",
  "message": "Perfil actualizado",
  "data": {
    "first_name": "Juan Carlos",
    "last_name": "Pérez García"
  }
}
```

---

### 3. Cambiar Password (POST)

```http
POST /accounts/change-password/
Authorization: Bearer [token]
Content-Type: application/json

{
  "old_password": "OldPass123!",
  "new_password1": "NewPass456!",
  "new_password2": "NewPass456!"
}
```

**Respuesta (200)**
```json
{
  "status": "success",
  "message": "Contraseña actualizada"
}
```

**Error: Password vieja incorrecta (400)**
```json
{
  "status": "error",
  "error": "password_incorrect",
  "message": "La contraseña actual es incorrecta"
}
```

---

## 👨‍💼 ENDPOINTS DE ADMIN

### 1. Listar Usuarios Pendientes (GET)

```http
GET /admin/api/users/pending/
Authorization: Bearer [admin-token]
```

**Respuesta (200)**
```json
{
  "total": 5,
  "users": [
    {
      "id": 42,
      "email": "new@example.com",
      "first_name": "Nuevo",
      "created_at": "2026-02-19T08:00:00Z",
      "email_verified": true,
      "status": "pending"
    }
  ]
}
```

---

### 2. Aprobar Usuario (PATCH)

```http
PATCH /admin/api/users/{user_id}/approve/
Authorization: Bearer [admin-token]
Content-Type: application/json

{}
```

**Respuesta (200)**
```json
{
  "status": "success",
  "message": "Usuario aprobado",
  "user_id": 42,
  "email_notification_sent": true
}
```

---

### 3. Rechazar Usuario (PATCH)

```http
PATCH /admin/api/users/{user_id}/reject/
Authorization: Bearer [admin-token]
Content-Type: application/json

{
  "reason": "Email dominio sospechoso"
}
```

**Respuesta (200)**
```json
{
  "status": "success",
  "message": "Usuario rechazado",
  "user_id": 42,
  "email_notification_sent": true
}
```

---

### 4. Deshabilitar Usuario (PATCH)

```http
PATCH /admin/api/users/{user_id}/disable/
Authorization: Bearer [admin-token]
Content-Type: application/json

{
  "reason": "Comportamiento sospechoso"
}
```

**Respuesta (200)**
```json
{
  "status": "success",
  "message": "Usuario deshabilitado",
  "user_id": 42
}
```

---

## 🔄 CÓDIGOS DE ERROR

### Códigos HTTP

| Código | Significado |
|--------|------------|
| 200 | OK - Solicitud exitosa |
| 201 | Created - Recurso creado |
| 400 | Bad Request - Datos inválidos |
| 401 | Unauthorized - No autenticado |
| 403 | Forbidden - No permitido |
| 404 | Not Found - Recurso no existe |
| 409 | Conflict - Recurso ya existe |
| 500 | Server Error - Error servidor |

### Códigos de Error Personalizados

```javascript
// Email
EMAIL_NOT_VERIFIED      // Usuario no verificó email
EMAIL_ALREADY_VERIFIED  // Email ya fue verificado
EMAIL_DUPLICATE         // Email ya registrado

// Aprobación
PENDING_APPROVAL        // Usuario pendiente de aprobación
REJECTED                // Usuario rechazado
DISABLED                // Usuario deshabilitado
APPROVAL_EXPIRED        // Aprobación expiró

// Auth
PASSWORD_INCORRECT      // Password incorrecto
TOKEN_INVALID           // Token inválido
TOKEN_EXPIRED           // Token expirado
SESSION_EXPIRED         // Sesión expirada

// Validación
PASSWORD_WEAK           // Password muy débil
PASSWORDS_MISMATCH      // Passwords no coinciden
INVALID_EMAIL           // Email inválido
MISSING_REQUIRED_FIELD  // Campo requerido falta
```

---

## 📝 EJEMPLOS DE INTEGRACIÓN

### JavaScript/Fetch

```javascript
// Registro
async function register(email, password1, password2, firstName, lastName) {
  const response = await fetch('/accounts/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email, password1, password2, first_name: firstName, last_name: lastName
    })
  });
  return response.json();
}

// Login
async function login(email, password) {
  const response = await fetch('/accounts/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  if (data.status === 'error') {
    // Manejar error
    console.error(data.message);
  }
  return data;
}

// Verificar email
async function verifyEmail(token) {
  const response = await fetch('/accounts/verify-email/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  });
  return response.json();
}
```

### Python/Requests

```python
import requests

# Configuración
BASE_URL = 'http://127.0.0.1:8000'
session = requests.Session()

# Registro
def register(email, password, first_name, last_name):
    response = session.post(f'{BASE_URL}/accounts/register/', json={
        'email': email,
        'password1': password,
        'password2': password,
        'first_name': first_name,
        'last_name': last_name
    })
    return response.json()

# Login
def login(email, password):
    response = session.post(f'{BASE_URL}/accounts/login/', json={
        'email': email,
        'password': password
    })
    return response.json()

# Obtener perfil
def get_profile():
    response = session.get(f'{BASE_URL}/accounts/profile/')
    return response.json()
```

### cURL

```bash
# Registro
curl -X POST http://127.0.0.1:8000/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password1": "Pass123!",
    "password2": "Pass123!",
    "first_name": "Juan",
    "last_name": "Pérez"
  }'

# Login
curl -X POST http://127.0.0.1:8000/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Pass123!"
  }' \
  -c cookies.txt

# Obtener perfil (con cookies)
curl http://127.0.0.1:8000/accounts/profile/ \
  -b cookies.txt
```

---

## 🔒 SEGURIDAD EN INTEGRACIÓN

### HTTPS Requerido (Producción)

```
❌ NUNCA: http://api.fenix.com/login
✅ SIEMPRE: https://api.fenix.com/login
```

### Manejo de Tokens

```javascript
// MALO - Tokens en localStorage
localStorage.setItem('auth_token', token); // Vulnerable a XSS

// MEJOR - Tokens en httpOnly cookies
// El servidor lo establece automáticamente
```

### Validación de Input

```javascript
// MALO
const email = userInput; // Sin validación

// MEJOR
const email = userInput.trim().toLowerCase();
if (!isValidEmail(email)) {
  throw new Error('Email inválido');
}
```

### Rate Limiting

Fenix implementa rate limiting en:
- `/accounts/register/` - 5 intentos por hora
- `/accounts/login/` - 10 intentos por hora
- `/accounts/resend-verification-email/` - 3 intentos por hora

En caso de límite excedido:
```json
{
  "status": "error",
  "message": "Demasiados intentos, intenta más tarde",
  "retry_after_seconds": 300
}
```

---

## 🧪 TESTING

### Test de Registro

```python
def test_user_registration():
    response = client.post('/accounts/register/', {
        'email': 'test@example.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User'
    })
    assert response.status_code == 200
    assert response.json()['status'] == 'success'

def test_duplicate_email():
    client.post('/accounts/register/', {...})
    response = client.post('/accounts/register/', {
        'email': 'test@example.com',  # Duplicado
        ...
    })
    assert response.status_code == 400
    assert 'Email ya está registrado' in response.json()['errors']

def test_weak_password():
    response = client.post('/accounts/register/', {
        'password1': '123',  # Muy débil
        'password2': '123',
        ...
    })
    assert response.status_code == 400
```

---

## 📞 SOPORTE

### Problemas Comunes en Integración

**P: El email de verificación no llega**
R: Verifica que el servidor esté configurado para enviar emails

**P: ¿Cómo almaceno el token?**
R: En httpOnly cookies (seguro) o localStorage si no hay opción

**P: ¿Cada cuánto caduca el token?**
R: Sesión: 30 días inactividad | Token: 90 días

**P: ¿Puedo hacer login sin verificar email?**
R: No, obligatorio para seguridad

---

## 📊 CHANGELOG

**v1.0 (2026-02-19)**
- Endpoints iniciales
- Autenticación dual-gate
- Email verification y approval system

**v1.1 (Planeado)**
- OAuth2 support
- API Key authentication
- Rate limiting por IP
- Webhooks para eventos

---

**Última actualización**: 19 de febrero, 2026
**Versión**: 1.0
**Para**: Desarrolladores integrando Fenix

---

¿Tienes preguntas sobre la API? Contacta a **dev-support@fenix.com**
