# 👨‍💼 GUÍA PARA ADMINISTRADORES - APROBACIÓN DE USUARIOS

## Para Admins y Moderadores

Esta guía explica cómo revisar, aprobar y rechazar solicitudes de nuevos usuarios en Fenix.

---

## 🎯 Rol del Administrador

### Mi Responsabilidad

Como administrador de Fenix, eres responsable de:

1. **Revisar solicitudes** - Verificar que usuarios sean legítimos
2. **Aprobar usuarios válidos** - Darles acceso a la plataforma
3. **Rechazar usuarios inválidos** - Denegar acceso a bots, spam, etc.
4. **Deshabilitar cuentas** - Bloquear usuarios problemáticos
5. **Monitorear actividad** - Verificar que todo funcione correctamente

---

## 📊 Dashboard de Administración

### Acceder al Dashboard

1. Navega a: **http://127.0.0.1:8000/admin/**
2. Login con tus credenciales de admin
3. Verás el panel de administración de Django

### Secciones Principales

```
Admin Dashboard
├── Accounts
│   ├── Users                  ← Aquí revisas usuarios
│   ├── Groups
│   └── Permissions
├── Catalog
├── Orders
└── ... (otras secciones)
```

---

## 🔍 REVISAR USUARIOS PENDIENTES

### Paso 1: Acceder a la lista de usuarios

1. En admin dashboard, haz clic en **"Accounts"** → **"Users"**
2. Verás una lista de todos los usuarios

### Paso 2: Identificar usuarios pendientes

Busca en la columna "status":
- 🟡 **pending** = Esperando tu aprobación
- 🟢 **active** = Ya aprobados
- 🔴 **rejected** = Rechazados
- ⛔ **disabled** = Deshabilitados

### Paso 3: Filtrar por estado

Usa el filtro en la derecha:
- Haz clic en "Status"
- Selecciona "pending"
- Verás solo usuarios pendientes

---

## ✅ APROBAR UN USUARIO

### Paso por Paso

#### Método 1: Edición Rápida (Recomendado)

1. Abre la lista de usuarios pendientes
2. Haz clic en el usuario a aprobar (ej. `testuser@example.com`)
3. En el formulario, busca el campo "status"
4. Cambia de **"pending"** a **"active"**
5. Observa que se llenen automáticamente:
   - `approved_by`: Tu nombre (admin)
   - `approved_at`: Fecha y hora actual
6. Haz clic en **"Save"** (o "Save and continue editing")

#### Método 2: Cambio en Lote (Para múltiples)

Si tienes muchos usuarios:

1. En lista de usuarios
2. Selecciona los checkboxes de los usuarios
3. En dropdownabajo, selecciona la acción
4. Haz clic "Go"

### ¿Qué sucede automáticamente?

Cuando cambias status a "active":

✅ Sistema marca como aprobado
✅ Sistema registra quién aprobó (approved_by)
✅ Sistema registra cuándo (approved_at)
✅ Sistema envía email de aprobación al usuario
✅ Usuario ahora puede iniciar sesión

---

## ❌ RECHAZAR UN USUARIO

### Paso a Paso

1. Abre el usuario a rechazar
2. Campo "status": Cambia a **"rejected"**
3. Haz clic en **"Save"**

### ¿Qué sucede?

✅ Usuario recibe email: *"Tu solicitud ha sido rechazada"*
✅ Usuario NUNCA puede iniciar sesión (estado permanente)
✅ Usuario puede contactar soporte si cree que es error

### ¿Cómo sabe el usuario por qué fue rechazado?

El email incluye instrucciones para contactar soporte. Para proporcionar mayor detalle, puedes:

**Opción A**: Agregar nota en admin comments
**Opción B**: Contactar al usuario manualmente por email

**Futuro**: Se planea agregar campo de "motivo de rechazo"

---

## ⛔ DESHABILITAR UN USUARIO

### Cuándo Deshabilitar

Usa este estado para bloquear temporalmente a usuarios que:
- Violaron términos de servicio
- Comportamiento sospechoso
- Solicitud de usuario
- Mantenimiento de cuenta

### Cómo Deshabilitar

1. Abre el usuario
2. Field "status": Cambiar a **"disabled"**
3. Guardar

### Diferencia entre Rejected y Disabled

| Rejected | Disabled |
|----------|----------|
| Permanente | Temporal |
| Usuario rechazado definitivamente | Usuario pausado |
| No puede revertirse (sin admin manual) | Puede revertirse a "active" |
| Email explica rechazo | Notificar por otro medio |

---

## 📧 EMAILS ENVIADOS AUTOMÁTICAMENTE

### Email de Aprobación

**Datos:**
- Enviado a: Dirección de email del usuario
- Cuándo: Inmediatamente después de cambiar status a "active"
- Asunto: "¡Tu cuenta ha sido aprobada!"

**Contenido:**
```
¡Hola [Nombre del Usuario]!

Tu cuenta en Fenix ha sido **aprobada exitosamente**.

Ya puedes iniciar sesión en:
https://platform.fenix.com/accounts/login/

Tu email: [su email]

Si tienes preguntas, contáctanos a:
soporte@plataformafenix.com

¡Bienvenido a Fenix!
```

### Email de Rechazo

**Datos:**
- Enviado a: Dirección de email
- Cuándo: Inmediatamente después de cambiar status a "rejected"
- Asunto: "Tu solicitud ha sido rechazada"

**Contenido:**
```
Hola [Nombre del Usuario],

Lamentablemente, tu solicitud de acceso a Fenix ha sido **rechazada**.

Si crees que esto es un error, por favor contacta a:
soporte@plataformafenix.com

Equipo Fenix
```

---

## 🔧 EDITAR OTROS CAMPOS

Además de "status", puedes editar:

### Datos del Usuario
- **Email**: Úsalo con cuidado (afecta login)
- **Nombre**: Actualizar información
- **Apellido**: Actualizar información
- **Password**: Si olvidó o necesita reset

### Campos de Seguridad
- **email_verified**: ¿Ha verificado email?
- **status**: Estado de cuenta
- **approved_by**: Quién aprobó (auto-llenado)
- **approved_at**: Cuándo aprobó (auto-llenado)

### Permisos
- **is_staff**: ¿Es miembro de staff?
- **is_superuser**: ¿Es superadmin?
- **Groups**: Asignar a grupos

---

## 📊 ESTADÍSTICAS IMPORTANTES

### Información que Verás

```
Para cada usuario:
- Email (login)
- Nombre completo
- Status (pending|active|rejected|disabled)
- Email verificado (Sí/No)
- Fecha de registro (created)
- Aprobado por (nombre de admin)
- Fecha de aprobación
- Última conexión
- Activo (Sí/No)
```

### Búsqueda y Filtros

**Buscar por:**
- Email exacto: `user@example.com`
- Nombre: `Juan Pérez`
- Status: Filter → Status

**Ordenar por:**
- Haz clic en encabezados de columna
- Fecha más reciente primero (default)

---

## ⚠️ ADVERTENCIAS Y MEJORES PRÁCTICAS

### ✅ QUÉ HACER

- ✅ Revisar email antes de aprobar (¿es legítimo?)
- ✅ Aprobar dentro de 24-48 horas
- ✅ Documentar motivo si rechazas
- ✅ Contactar usuario si hay duda
- ✅ Revisar intentos de login fallidos
- ✅ Monitorear cuentas nuevas durante primeros días

### ❌ NO HACER

- ❌ Aprobar sin revisar (podrían ser bots)
- ❌ Cambiar email de usuario sin consentimiento
- ❌ Deshabilitar sin motivo o aviso
- ❌ Aprobar cuentas sospechosas
- ❌ Shared admin credentials
- ❌ Olvidar documentar cambios importantes

---

## 🔐 SEGURIDAD DEL ADMIN

### Tu Cuenta es Especial

Como admin, tienes acceso a:
- Todas las cuentas de usuarios
- Información sensible
- Funciones de cambio de estado

### Protege tu Cuenta Admin

1. **Contraseña fuerte**: Mínimo 12 caracteres
2. **Cambio regular**: Actualiza cada 90 días
3. **2-FA**: Si disponible, habilitar
4. **Logs**: Revisa acceso al admin regularmente
5. **No compartir**: Nunca compartas credenciales

### Auditoría

Todos tus cambios quedan registrados:
- approved_by: Sabe quién aprobó
- approved_at: Sabe cuándo
- Logs: Sistema registra todas las acciones

---

## 🆘 PROBLEMAS COMUNES

### Problema 1: "No puedo acceder a admin"

**Solución:**
1. Verifica que eres superuser: `is_superuser=True`
2. Verifica que eres staff: `is_staff=True`
3. Inicia sesión nuevamente
4. Borra cookies del navegador

### Problema 2: "Usuario no es logueado después de aprobar"

**Causa correcta**: Requiere que cierre sesión y abra nueva

**Solución:**
- Notify al usuario: "Tu cuenta fue aprobada, por favor login de nuevo"

### Problema 3: "Email de aprobación no llegó"

**Verificar:**
1. Revisa configuración de email en settings.py
2. Revisa logs del servidor
3. Verifica email del usuario (¿es correcto?)

**Solución temporal:**
- Contacta al usuario manualmente
- Confirma que su email es correcto

### Problema 4: "¿Puedo cambiar un usuario rechazado a activo?"

**Respuesta**: Sí, pero no se recomienda
- Cambiar status de "rejected" a "active"
- Este usuario ya recibió email de rechazo
- Se recomienda contactarlo primero

---

## 📋 CHECKLIST DIARIO

Al iniciar tu turno como admin:

- [ ] Acceder a /admin/
- [ ] Ir a Accounts → Users
- [ ] Filtrar por status="pending"
- [ ] Revisar cada solicitud pendiente
- [ ] Aprobar usuarios legítimos
- [ ] Rechazar usuarios sospechosos
- [ ] Documentar cualesquiera notas
- [ ] Monitorear usuarios activos
- [ ] Revisar logs si hay problemas

---

## 📞 CONTACTO Y ESCALACIONES

### Si Tienes Duda sobre un Usuario

1. **Investigar**: ¿Email sospechoso? ¿Nombre genérico?
2. **Contactar**: Send email al usuario pidiendo validación
3. **Esperar**: Dale 24-48 horas para responder
4. **Decidir**: Aprobar o rechazar

### Escalaciones

Para problemas que no sabes resolver:
- Contacta tech lead
- Contacta outro admin
- Escalada a director

---

## 📊 REPORTES (Futuro)

Próximamente disponibles:
- [ ] Dashboard de usuarios por estado
- [ ] Tiempo promedio de aprobación
- [ ] Estadísticas de rechazo
- [ ] Usuarios más activos
- [ ] Intentos fallidos de login

---

## 🎓 CAPACITACIÓN ADICIONAL

### Temas relacionados

Para más información sobre:
- **Seguridad general**: Ver DOCUMENTACION_SEGURIDAD.md
- **Sistema de permisos**: Contacta a lead developer
- **RBAC avanzado**: Documentación de Django
- **Auditoría y logs**: Contacta DevOps

---

## ✅ Resumen

Tu trabajo como admin es simple pero crítico:

1. **Revisar** solicitudes de usuarios
2. **Aprobar** los legítimos
3. **Rechazar** los sospechosos
4. **Monitorear** la plataforma

Esto protege a Fenix de:
- Bots y spam
- Registros inválidos
- Acceso no autorizado
- Abuso de plataforma

**Eres la primera línea de defensa de la seguridad de Fenix** 🛡️

---

## 📝 Notas Finales

- Cambios se aplican **inmediatamente**
- Emails se envían **automáticamente**
- Todo queda **registrado** en base de datos
- Puedes **revertir** cambios si necesario
- Contacta soporte si necesitas **recuperación de datos**

---

**Versión**: 1.0
**Última actualización**: 19 de febrero, 2026
**Para**: Administradores y moderadores

¡Gracias por mantener Fenix seguro! 🙏
