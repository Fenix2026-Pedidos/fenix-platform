# FENIX - Requisitos MVP (7 Puntos Clave)

## 1. Visión General
FENIX es una plataforma B2B single-tenant, orientada a la gestión operativa de pedidos sin pasarela de pago, con:
- Catálogo tipo ecommerce (compartido por todos los usuarios)
- Gestión completa del ciclo de vida del pedido
- Pedidos recurrentes / programados
- Backoffice operativo para managers
- Gestión básica de stock (solo manager)
- Notificaciones automáticas por eventos/estados
- Soporte multilenguaje Español / Chino Simplificado
- Arquitectura preparada para IA y escalado

👉 El proceso finaliza cuando el pedido está ENTREGADO y con VALIDACIONES FINALES OK.

## 2. Principios Clave del MVP
- ❌ No hay pagos ni "estado pagado"
- ✅ Éxito = pedido entregado + validaciones finales OK
- 🔁 Pedidos recurrentes incluidos desde el MVP
- 📦 Stock incluido solo para control operativo (no ERP)
- 🌍 i18n obligatorio en paralelo (ES / zh-CN)
- 🔐 Roles claros y mínimos
- 🚀 Simplicidad + Time-to-Value

## 3. Regla de Oro de Desarrollo (OBLIGATORIA)
### 🌍 i18n
Una funcionalidad NO está terminada si no existe en Español y Chino Simplificado.
Incluye:
- UI
- Estados
- Emails
- Errores
- Notificaciones
- Productos
- Validaciones

❌ Prohibido hardcodear textos
✅ Uso obligatorio de i18n (es / zh-CN) con fallback
✅ Aislamiento por usuario (single-tenant)

Cualquier feature es incorrecta si no aplica correctamente los filtros de acceso:
- Usuario (Cliente): solo ve sus datos (user_id)
- Manager / Super Admin: ven todos los datos de la plataforma

En single-tenant no existe org_id. El control se hace por roles y owner (user_id).

### 📝 Formateo de Código (HTML/Django)
❌ **PROHIBIDO:** Usar formateadores automáticos (como Prettier o el de VSCode) en archivos `.html` que contengan etiquetas de Django (`{% %}` o `{{ }}`).
- El autoformateador rompe las etiquetas largas (ej. `blocktrans`) en múltiples líneas, provocando un `TemplateSyntaxError` (Error 500).
- La regla es **escribir HTML de forma manual** respetando la sintaxis del lenguaje de plantillas de Django, usar variables cortas o tener apagado el `formatOnSave` en el entorno para archivos HTML (ya forzado por `.vscode/settings.json` y `.prettierignore`).

## 4. Modelo SINGLE-TENANT (sin organizaciones ni suscripción por tenant)
- Existe una única instancia de FENIX para un único negocio.
- Todos los usuarios ven el mismo catálogo, precios y stock global.
- El "modelo de suscripción" (si aplica) es a nivel plataforma (opcional) y no por organización.

## 5. Roles del Sistema
### 🟣 Super Admin (Global)
- Control total de la plataforma
- Gestión de usuarios y managers
- Auditoría y soporte
- Configuración global (idioma por defecto, email remitente, etc.)

### 🔵 Administrador / Manager
- Backoffice operativo
- Gestión de pedidos y estados
- Gestión de productos y stock
- Gestión de usuarios (aprobación/activación)
- Validaciones y ETA

### 🟢 Usuario (Cliente)
- Ver catálogo
- Crear pedidos
- Crear pedidos recurrentes
- Ver seguimiento de sus pedidos
- Ver su documentación asociada (por pedido)

## 6. Modelo de Registro (reutilizado de HR Talent)
Flujo:
1. Registro (email, password, nombre, idioma)
2. Verificación de email
3. Estado: pendiente de aprobación
4. Aprobación por Manager o Super Admin
5. Acceso según rol

Estados de usuario:
- `email_verified`
- `pending_approval`
- `active`

## 7. Checklist de Implementación

### ✅ Completado
- [x] Modelo User con roles (Super Admin, Manager, Client)
- [x] Modelo User con estados (email_verified, pending_approval, is_active)
- [x] Configuración i18n en settings.py (es / zh-hans)
- [x] Archivos .po creados (es / zh_Hans)
- [x] Templates usando {% trans %}
- [x] Modelo PlatformSettings para configuración global
- [x] Notificaciones con soporte i18n

### 🔄 Pendiente
- [ ] Verificación de email con token
- [ ] Vista de aprobación de usuarios para Managers
- [ ] Middleware/decorador para bloquear acceso si pending_approval=True
- [ ] Filtros de acceso: Managers ven todos los pedidos, Clientes solo los suyos
- [ ] Verificar/eliminar referencias a organizaciones (single-tenant)
- [ ] Completar traducciones en archivos .po
- [ ] Compilar mensajes i18n (compilemessages)
- [ ] Asegurar que todos los mensajes de error usen i18n
