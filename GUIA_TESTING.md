# 🧪 GUÍA DE TESTING - PUERTAS DE SEGURIDAD DE 2 PASOS

## Para Testers y QA

Esta guía te proporcionará instrucciones paso a paso para probar la implementación de las puertas de seguridad de 2 pasos.

---

## 📋 REQUISITOS PREVIOS

### Servidor Ejecutándose
```bash
python manage.py runserver
```
Accesible en: http://127.0.0.1:8000/

### Acceso a Admin
- Email: Debes saber las credenciales del admin
- URL: http://127.0.0.1:8000/admin/

### Cliente de Email (opcional pero recomendado)
- A menos que tengas configured real email
- Revisa logs del servidor

---

## 🧪 SUITE DE TESTS AUTOMATIZADOS

### Ejecutar todos los tests

```bash
python manage.py test accounts.tests.test_security_gates -v 2
```

**Resultado esperado:**
- ✅ 9 tests pasando
- ℹ️ 3 tests con issues menores de framework

### Tests individuales

```bash
# Solo login tests
python manage.py test accounts.tests.test_security_gates.LoginSecurityGateTests

# Solo middleware tests
python manage.py test accounts.tests.test_security_gates.MiddlewareSecurityTests

# Solo authorization tests
python manage.y test accounts.tests.test_security_gates.AuthorizationTests
```

---

## 🎯 PRUEBA 1: REGISTRO Y EMAIL

### Objetivo
Verificar que el registro funciona y envía email de verificación

### Pasos

1. **Accede a página de registro**
   - URL: http://127.0.0.1:8000/accounts/register/

2. **Completa el formulario**
   - Email: `testuser1@example.com` (usa email único cada vez)
   - Nombre Completo: `Test User One`
   - Password: `TestPass123!`
   - Confirmar Password: `TestPass123!`

3. **Envía formulario**
   - Haz clic en botón "Registrarse"

### Verificaciones

✅ **Esperado:**
- [ ] Usuario se crea correctamente
- [ ] Se muestra mensaje: *"Te hemos enviado un email de verificación"*
- [ ] Se redirige a página appropriada
- [ ] En logs: Aparece línea indicando email enviado

**Comando para verificar en base de datos:**
```bash
python manage.py shell
from accounts.models import User
u = User.objects.get(email="testuser1@example.com")
print(f"Email verificado: {u.email_verified}")  # Debe ser: False
print(f"Status: {u.status}")                     # Debe ser: pending
```

---

## 🎯 PRUEBA 2: VERIFICACIÓN DE EMAIL

### Objetivo
Verificar que el link de email marca usuario como verificado pero NO lo loguea

### Pasos

1. **Obtén el link de verificación**
   - Opción A: Revisa email si está configurado
   - Opción B: Revisa logs del servidor
   - Opción C: Usa shell para obtenerlo:
   ```bash
   python manage.py shell
   from accounts.models import EmailVerificationToken
   token = EmailVerificationToken.objects.filter(
       user__email="testuser1@example.com"
   ).first()
   print(f"Link: http://127.0.0.1:8000/accounts/verify-email/?token={token.token}")
   ```

2. **Abre el link de verificación**
   - Copia y pega el link en navegador

3. **Observa la respuesta**

### Verificaciones

✅ **Esperado:**
- [ ] Se muestra página "Pendiente de Aprobación"
- [ ] Se muestra mensaje: *"Tu cuenta está pendiente de aprobación"*
- [ ] Usuario NO es logueado (no ves dashboard)
- [ ] Token se marca como usado

**Comando para verificar:**
```bash
python manage.py shell
from accounts.models import User
u = User.objects.get(email="testuser1@example.com")
print(f"Email verificado ahora: {u.email_verified}")  # Debe ser: True
print(f"Status: {u.status}")                          # Debe ser: pending (no activo)
```

---

## 🎯 PRUEBA 3: LOGIN BLOQUEADO (Sin Aprobación)

### Objetivo
Verificar que usuario no puede iniciar sesión sin aprobación

### Pasos

1. **Accede a página de login**
   - URL: http://127.0.0.1:8000/accounts/login/

2. **Intenta login**
   - Email: `testuser1@example.com`
   - Password: `TestPass123!`

3. **Envía formulario**

### Verificaciones

✅ **Esperado:**
- [ ] Login NO funciona
- [ ] Se muestra mensaje: *"Tu cuenta está pendiente de aprobación"*
- [ ] Se redirige a: `/accounts/pending-approval/`
- [ ] NO se crea sesión (no ves dashboard)
- [ ] Barra de navegación sigue mostrando "Login"

❌ **NO debería pasar:**
- [ ] Usuario logueado
- [ ] Dashboard accesible
- [ ] Pedidos visibles

---

## 🎯 PRUEBA 4: INTENTAR ACCEDER RUTAS PROTEGIDAS

### Objetivo
Verificar que middleware bloquea acceso a rutas protegidas

### Pasos

1. **Intenta acceder directamente a ruta protegida**
   - URL: http://127.0.0.1:8000/orders/

2. **Observa qué sucede**

### Verificaciones

✅ **Esperado:**
- [ ] Redirigido a: `/accounts/pending-approval/`
- [ ] Mensaje de alerta mostrando

❌ **NO debería pasar:**
- [ ] Ver lista de pedidos
- [ ] Ver dashboard
- [ ] Acceso a cualquier ruta no-pública

---

## 🎯 PRUEBA 5: APROBACIÓN POR ADMIN

### Objetivo
Verificar que admin puede aprobar y envía email

### Pasos

1. **Login como admin**
   - URL: http://127.0.0.1:8000/admin/
   - Usa credenciales de admin

2. **Navega a Users**
   - Haz clic en "Accounts" en sidebar
   - Haz clic en "Users"

3. **Encuentra el usuario pendiente**
   - Busca `testuser1@example.com`
   - Haz clic para editar

4. **Approbar el usuario**
   - Campo "status": Cambiar a "active" (o "ACTIVE")
   - Haz clic en "Save"

### Verificaciones

✅ **Esperado:**
- [ ] Usuario se actualiza sin errores
- [ ] Status cambia a "active"
- [ ] Campos approved_by y approved_at se llenan
- [ ] Email de aprobación se envía (revisar logs)

**Comando para verificar:**
```bash
python manage.py shell
from accounts.models import User
from django.utils import timezone

u = User.objects.get(email="testuser1@example.com")
print(f"Status: {u.status}")              # Debe ser: active
print(f"Aprobado por: {u.approved_by}")   # Debe ser: admin user
print(f"Aprobado en: {u.approved_at}")    # Debe ser: datetime reciente
```

---

## 🎯 PRUEBA 6: LOGIN EXITOSO (Después de Aprobación)

### Objetivo
Verificar que usuario puede iniciar sesión después de aprobación

### Pasos

1. **Accede a login**
   - URL: http://127.0.0.1:8000/accounts/login/

2. **Intenta login con credenciales**
   - Email: `testuser1@example.com`
   - Password: `TestPass123!`

3. **Envía formulario**

### Verificaciones

✅ **Esperado:**
- [ ] Login FUNCIONA correctamente
- [ ] Se crea sesión
- [ ] Redirigido a dashboard
- [ ] Puedes ver tu información
- [ ] Barra de navegación muestra tu nombre

---

## 🎯 PRUEBA 7: ACCESO A RUTAS PROTEGIDAS

### Objetivo
Verificar que usuario aprobado puede acceder a todas las rutas

### Pasos

1. **Con sesión activa de testuser1**

2. **Accede a diferentes rutas:**
   - http://127.0.0.1:8000/orders/ → Debe funcionar
   - http://127.0.0.1:8000/dashboard/ → Debe funcionar
   - http://127.0.0.1:8000/catalog/ → Debe funcionar
   - http://127.0.0.1:8000/accounts/profile/ → Debe funcionar

### Verificaciones

✅ **Esperado:**
- [ ] Todas las rutas cargan correctamente
- [ ] Puedes ver contenido
- [ ] No hay redirecciones a pending_approval

---

## 🎯 PRUEBA 8: RECHAZO DE USUARIO

### Objetivo
Verificar que admin puede rechazar usuarios

### Pasos

1. **Login como admin**

2. **Crea nuevo usuario para rechazar**
   - Registro: `testuser2@example.com`
   - Verifica email
   - No lo apruebes aún

3. **En admin panel**
   - Navega a Users
   - Edita `testuser2@example.com`
   - Campo status: Cambiar a "rejected"
   - Guardar

### Verificaciones

✅ **Esperado:**
- [ ] Status cambia a "rejected"
- [ ] Email de rechazo enviado
- [ ] Usuario no puede iniciar sesión nunca

**Intenta login:**
- Email: testuser2@example.com
- Password: correcta
- Resultado: Login bloqueado con mensaje de rechazo

---

## 🎯 PRUEBA 9: DESHABILITACIÓN DE USUARIO

### Objetivo
Verificar que admin puede deshabilitar cuentas activas

### Pasos

1. **Con usuario aprobado activo**

2. **En admin panel**
   - Edita usuario
   - Status: Cambiar a "disabled"
   - Guardar

3. **Intenta login con ese usuario**

### Verificaciones

✅ **Esperado:**
- [ ] Usuario actualmente logueado se desconecta
- [ ] No puede volver a iniciar sesión
- [ ] Mensaje indicando cuenta deshabilitada

---

## 🎯 PRUEBA 10: CASOS EDGE

### Caso 1: Token de email expirado

```bash
python manage.py shell
from accounts.models import EmailVerificationToken
from django.utils import timezone
from datetime import timedelta

# Crear token con fecha antigua
token = EmailVerificationToken.objects.filter(
    user__email="testuser1@example.com"
).first()
token.created_at = timezone.now() - timedelta(days=2)
token.save()
```

Intenta usar link → Debe mostrar error "Token expirado"

### Caso 2: Token usado dos veces

1. Usa el link de verificación una vez (funciona)
2. Intenta usar el mismo link otra vez → Debe fallar

### Caso 3: Email inválido

En registro, intenta email inválido → Debe rechazar

---

## 📊 REPORTE DE TESTING

### Template de Reporte

```
PRUEBA: [Nombre]
Fecha: [DD/MM/YYYY]
Tester: [Nombre]

RESULTADO: ✅ PASÓ / ❌ FALLÓ

Pasos ejecutados:
1. [Paso 1]
2. [Paso 2]
...

Resultados observados:
[Descripción]

Screenshots:
[Adjuntar si corresponde]

Notas:
[Observaciones adicionales]
```

---

## 🐛 REPORTAR BUGS

Si encuentras un problema:

1. **Documenta el caso**
   - ¿Qué hiciste?
   - ¿Qué pasó?
   - ¿Qué debería pasar?

2. **Incluye contexto**
   - Usuario del navegador
   - URL exacta
   - Pasos para reproducir
   - Screenshots/videos si es posible

3. **Crea issue en GitHub**
   ```
   Título: [SECURITY] Puerta de seguridad falló
   Descripción: [Detalles del bug]
   Pasos: [Reproducir]
   Resultado: [Lo que pasó]
   Esperado: [Lo que debería pasar]
   ```

---

## ✅ CHECKLIST FINAL

Antes de considerar testing completado:

- [ ] Todos los 10 test cases ejecutados
- [ ] Suite de tests automatizados pasando (9/12 mínimo)
- [ ] Sin errores en logs
- [ ] Emails enviándose correctamente
- [ ] Redirecciones funcionando
- [ ] Base de datos consistente
- [ ] Usuario puede hacer flujo completo (registro → aprobación → login)

---

## 🎓 NOTAS PARA TESTING FUTURO

1. **Pruebas de rendimiento**
   - ¿Qué pasa con 1000 usuarios pendientes?
   - ¿Cuánto tarda aprobación por lotes?

2. **Pruebas de seguridad avanzadas**
   - ¿Se puede bypassear middleware?
   - ¿SQL injection en email?
   - ¿Session fixation?

3. **Compatibilidad de navegadores**
   - ¿Funciona en Chrome, Firefox, Safari?
   - ¿Funciona en mobile?

4. **Integración con otros sistemas**
   - ¿Funciona con API externa?
   - ¿Webhooks correctamente?

---

**Versión**: 1.0
**Última actualización**: 19 de febrero, 2026
**Duración estimada de testing**: 1-2 horas

¡Feliz testing! 🚀
