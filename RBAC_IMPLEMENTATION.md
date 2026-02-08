# 🔒 SISTEMA RBAC (ROLES Y PERMISOS) - IMPLEMENTACIÓN COMPLETA

## ✅ ESTADO: IMPLEMENTACIÓN COMPLETADA Y PROBADA

Fecha: 3 de Febrero, 2026  
Versión: 1.0  
Plataforma: Fenix (Django 6.0.1 + SQLite)

---

## 📋 RESUMEN EJECUTIVO

Se ha implementado exitosamente un sistema completo de **Control de Acceso Basado en Roles (RBAC)** que garantiza:

- ✅ **3 roles oficiales**: super_admin, admin, user
- ✅ **Permisos a nivel de backend**: Decoradores y helpers de validación
- ✅ **Permisos a nivel de frontend**: Filtros en templates y menús
- ✅ **Protección de SUPER_ADMIN**: Invisible para ADMIN
- ✅ **Asignación controlada de roles**: Solo desde Gestión de Usuarios
- ✅ **Migración de datos**: Actualización automática de roles antiguos

---

## 🎯 ROLES DEFINITIVOS

### 🟣 SUPER_ADMIN
**Permisos:**
- Control total de la plataforma
- Gestión de todos los usuarios (incluidos otros super_admin)
- Asignación de cualquier rol (super_admin, admin, user)
- Configuración global del sistema
- Acceso a administración Django

**Restricciones:**
- NO puede eliminarse a sí mismo

---

### 🔵 ADMIN
**Permisos:**
- Gestión de pedidos y estados
- Gestión de productos y catálogo
- Gestión de usuarios (solo admin y user)
- Aprobar/rechazar nuevos usuarios
- Activar/desactivar usuarios
- Asignar roles (solo admin y user)

**Restricciones:**
- NO puede ver usuarios super_admin
- NO puede editar usuarios super_admin
- NO puede eliminar usuarios super_admin
- NO puede asignar rol super_admin
- NO puede acceder a configuración global

---

### 🟢 USER / CLIENT
**Permisos:**
- Ver catálogo de productos
- Crear pedidos
- Crear pedidos recurrentes
- Ver seguimiento de sus propios pedidos
- Ver documentación asociada a sus pedidos

**Restricciones:**
- NO puede ver backoffice
- NO puede ver Gestión de Usuarios
- NO puede ver pedidos de otros usuarios
- NO puede asignar roles
- Solo ve su propio perfil

---

## 🏗️ ARQUITECTURA TÉCNICA

### 1. Modelo de Datos (accounts/models.py)

```python
class User(AbstractBaseUser, PermissionsMixin):
    # Roles oficiales
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'
    
    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_USER, 'User'),
    ]
    
    # Campos principales
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    role = models.CharField(choices=ROLE_CHOICES, default=ROLE_USER)
    status = models.CharField(choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    # Métodos helper
    def is_super_admin(self) -> bool
    def is_admin(self) -> bool
    def is_user(self) -> bool
    def can_manage_users(self) -> bool
```

---

### 2. Módulo de Permisos (accounts/permissions.py)

#### Helpers de Identificación
```python
is_super_admin(user) -> bool
is_admin(user) -> bool
is_user(user) -> bool
can_manage_users(user) -> bool
```

#### Helpers de Validación
```python
can_edit_target(editor, target_user) -> bool
can_assign_role(editor, target_role) -> bool
can_delete_target(editor, target_user) -> bool
get_role_choices_for_user(user) -> list
get_visible_users_queryset(user, queryset) -> QuerySet
```

#### Decoradores de Protección
```python
@super_admin_required
@admin_required
@staff_required
```

---

### 3. Vistas Protegidas (accounts/views.py)

#### register_view()
- ✅ Siempre asigna `role=User.ROLE_USER`
- ✅ Status inicial: `STATUS_PENDING`
- ✅ NO muestra selector de rol

#### user_approval_list()
- ✅ Decorador `@admin_required`
- ✅ Filtra usuarios según rol del logado
- ✅ ADMIN no ve super_admin
- ✅ Pasa `available_role_choices` al template

#### user_update_view()
- ✅ Decorador `@admin_required`
- ✅ Valida `can_edit_target(editor, target)`
- ✅ Valida `can_assign_role(editor, new_role)`
- ✅ Bloquea cambios no autorizados

#### user_delete_view()
- ✅ Decorador `@admin_required`
- ✅ Valida `can_delete_target(editor, target)`
- ✅ Previene auto-eliminación
- ✅ Soft delete (status=disabled)

#### approve_user_view()
- ✅ Decorador `@admin_required`
- ✅ Solo aprueba status=pending
- ✅ NO cambia role automáticamente
- ✅ Envía email de notificación

#### reject_user_view()
- ✅ Decorador `@admin_required`
- ✅ Solo rechaza status=pending
- ✅ Envía email de notificación

---

### 4. Template con Filtros RBAC (user_approval_dashboard.html)

#### TAB 1: Usuarios Registrados
```django
{% for user in registered_users %}
    {# RBAC: Ocultar super_admin si usuario logado es ADMIN #}
    {% if not (user.role == 'super_admin' and not user_is_super_admin) %}
        {# Mostrar fila #}
        
        {# Botones de acción #}
        {% if user.role == 'super_admin' and not user_is_super_admin %}
            <span>Sin permisos</span>
        {% else %}
            <button>Editar</button>
            {% if user.id != request.user.id %}
                <button>Eliminar</button>
            {% endif %}
        {% endif %}
        
        {# Selector de roles dinámico #}
        <select name="role">
            {% for role_value, role_label in available_role_choices %}
                <option value="{{ role_value }}">{{ role_label }}</option>
            {% endfor %}
        </select>
    {% endif %}
{% endfor %}
```

#### TAB 2: Nuevos Usuarios
- ✅ Solo muestra `status=pending` y `role=user`
- ✅ Botón "Aprobar" deshabilitado si email no verificado
- ✅ Acciones: Aprobar / Rechazar

---

### 5. Menú Lateral (components/sidebar.html)

```django
{# RBAC: Solo SUPER_ADMIN y ADMIN ven Gestión de Usuarios #}
{% if user.role == 'super_admin' or user.role == 'admin' %}
<div class="sidebar-menu-item">
    <a href="{% url 'accounts:user_approval_list' %}">
        <i class="bi bi-person-check"></i>
        <span>Gestión de Usuarios</span>
    </a>
</div>
{% endif %}

{# Administración Django solo para staff #}
{% if user.is_staff %}
<div class="sidebar-menu-item">
    <a href="{% url 'admin:index' %}">
        <i class="bi bi-gear"></i>
        <span>Administración</span>
    </a>
</div>
{% endif %}
```

---

### 6. Formulario de Registro (accounts/forms.py)

```python
class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('full_name', 'email', 'company')
        # ✅ NO incluye 'role'
```

**Vista register_view() asegura:**
```python
user.role = User.ROLE_USER  # SIEMPRE user en registro público
user.status = User.STATUS_PENDING
```

---

## 🔄 MIGRACIÓN DE DATOS

### Migration 0006: update_role_values

**Propósito:** Actualizar roles antiguos a los nuevos valores

```python
def update_role_values(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    
    # 'manager' → 'admin'
    User.objects.filter(role='manager').update(role='admin')
    
    # 'client' → 'user'
    User.objects.filter(role='client').update(role='user')
```

**Resultado de ejecución:**
```
✅ Migración de roles completada:
   - 0 usuarios 'manager' → 'admin'
   - 1 usuarios 'client' → 'user'
```

**Comando de ejecución:**
```bash
python manage.py migrate accounts
```

---

## 🧪 PRUEBAS DEL SISTEMA

### Script de Pruebas: test_rbac.py

**Casos de prueba:**

1. ✅ **Helpers de Roles**
   - is_super_admin(), is_admin(), is_user()
   - can_manage_users()

2. ✅ **Visibilidad de Usuarios**
   - SUPER_ADMIN ve todos (2 usuarios)
   - ADMIN ve todos excepto super_admin
   - USER ve solo sí mismo (1 usuario)

3. ✅ **Permisos de Edición**
   - SUPER_ADMIN puede editar cualquiera
   - ADMIN NO puede editar super_admin
   - USER NO puede editar otros

4. ✅ **Permisos de Eliminación**
   - SUPER_ADMIN NO puede eliminarse a sí mismo
   - ADMIN NO puede eliminar super_admin
   - ADMIN puede eliminar user

5. ✅ **Asignación de Roles**
   - SUPER_ADMIN puede asignar cualquier rol
   - ADMIN NO puede asignar super_admin
   - USER NO puede asignar roles

6. ✅ **Opciones de Roles**
   - SUPER_ADMIN ve 3 opciones
   - ADMIN ve 2 opciones (sin super_admin)
   - USER ve 0 opciones

**Ejecución:**
```bash
python test_rbac.py
```

**Resultado:**
```
✅ TODAS LAS PRUEBAS COMPLETADAS
```

---

## 🔐 REGLAS CRÍTICAS DE SEGURIDAD

### 1. Protección de SUPER_ADMIN

**Frontend:**
- ✅ INVISIBLE en lista de usuarios para ADMIN
- ✅ Botones de acción ocultos para ADMIN
- ✅ NO aparece en selector de roles para ADMIN

**Backend:**
- ✅ Filtrado con `get_visible_users_queryset()`
- ✅ Validación con `can_edit_target()`
- ✅ Validación con `can_delete_target()`
- ✅ Validación con `can_assign_role()`

### 2. Asignación de Roles

**Registro Público:**
- ✅ SIEMPRE role='user'
- ✅ SIEMPRE status='pending'
- ✅ NO muestra selector de rol

**Gestión de Usuarios:**
- ✅ Solo SUPER_ADMIN y ADMIN acceden
- ✅ Selector dinámico según permisos
- ✅ Validación backend antes de guardar

### 3. Flujo de Aprobación

**Nuevos Usuarios:**
1. Usuario se registra → role='user', status='pending'
2. Admin recibe email de notificación
3. Admin aprueba → status='active', role permanece 'user'
4. Usuario recibe email de aprobación
5. Usuario puede iniciar sesión

**Cambio de Rol:**
1. Solo desde Gestión de Usuarios
2. Solo por SUPER_ADMIN o ADMIN
3. ADMIN no puede asignar super_admin
4. Validación backend obligatoria

---

## 📊 MATRIZ DE PERMISOS

| Acción | SUPER_ADMIN | ADMIN | USER |
|--------|-------------|-------|------|
| Ver catálogo | ✅ | ✅ | ✅ |
| Crear pedidos | ✅ | ✅ | ✅ |
| Ver propios pedidos | ✅ | ✅ | ✅ |
| Ver todos los pedidos | ✅ | ✅ | ❌ |
| Acceder a Gestión de Usuarios | ✅ | ✅ | ❌ |
| Ver super_admin en lista | ✅ | ❌ | ❌ |
| Editar super_admin | ✅ | ❌ | ❌ |
| Editar admin | ✅ | ✅ | ❌ |
| Editar user | ✅ | ✅ | ❌ |
| Eliminar super_admin | ✅ | ❌ | ❌ |
| Eliminar admin | ✅ | ✅ | ❌ |
| Eliminar user | ✅ | ✅ | ❌ |
| Asignar role super_admin | ✅ | ❌ | ❌ |
| Asignar role admin | ✅ | ✅ | ❌ |
| Asignar role user | ✅ | ✅ | ❌ |
| Aprobar nuevos usuarios | ✅ | ✅ | ❌ |
| Rechazar nuevos usuarios | ✅ | ✅ | ❌ |
| Configuración global | ✅ | ❌ | ❌ |
| Administración Django | ✅ | ❌ | ❌ |

---

## 📁 ARCHIVOS MODIFICADOS/CREADOS

### Nuevos Archivos
```
accounts/permissions.py          # Sistema completo de helpers y decoradores RBAC
test_rbac.py                     # Script de pruebas del sistema
accounts/migrations/0006_update_role_values.py  # Migración de datos
```

### Archivos Modificados
```
accounts/models.py               # Actualizado: ROLE_ADMIN, ROLE_USER, métodos helper
accounts/views.py                # Actualizado: Decoradores, validaciones RBAC
accounts/forms.py                # Validado: NO incluye campo role
templates/accounts/user_approval_dashboard.html  # Filtros RBAC en frontend
templates/components/sidebar.html  # Visibilidad condicional del menú
```

---

## 🚀 DESPLIEGUE Y CONFIGURACIÓN

### 1. Aplicar Migración
```bash
cd "c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix"
python manage.py migrate accounts
```

### 2. Ejecutar Pruebas
```bash
python test_rbac.py
```

### 3. Verificar Sistema
- ✅ Registrar nuevo usuario → Debe ser role='user', status='pending'
- ✅ Login como ADMIN → NO debe ver super_admin en lista
- ✅ Login como ADMIN → NO debe poder asignar role='super_admin'
- ✅ Login como USER → NO debe ver "Gestión de Usuarios" en menú
- ✅ Aprobar usuario → Status cambia a 'active', role permanece 'user'

---

## 🔧 MANTENIMIENTO

### Crear Nuevo Usuario ADMIN
```python
from accounts.models import User

admin = User.objects.create_user(
    email='nuevo.admin@fenix.com',
    password='password_seguro',
    full_name='Nombre Admin',
    role=User.ROLE_ADMIN,
    status=User.STATUS_ACTIVE,
    email_verified=True
)
```

### Promover Usuario a ADMIN
```python
user = User.objects.get(email='usuario@fenix.com')
user.role = User.ROLE_ADMIN
user.save()
```

### Verificar Roles en BD
```python
from accounts.models import User

print(f"Super Admins: {User.objects.filter(role='super_admin').count()}")
print(f"Admins: {User.objects.filter(role='admin').count()}")
print(f"Users: {User.objects.filter(role='user').count()}")
```

---

## ⚠️ CONSIDERACIONES IMPORTANTES

1. **Backend es la Fuente de Verdad**
   - Todas las validaciones críticas están en el backend
   - Los filtros de frontend son solo UX, no seguridad

2. **Roles NO Cambian Automáticamente**
   - El registro siempre crea role='user'
   - El cambio de rol SOLO desde Gestión de Usuarios
   - La aprobación NO cambia el role

3. **SUPER_ADMIN Protegido**
   - ADMIN no puede verlos, editarlos, eliminarlos
   - Solo otro SUPER_ADMIN puede gestionar super_admin
   - El sistema previene escalación de privilegios

4. **Soft Delete**
   - La eliminación cambia status='disabled'
   - Los datos se mantienen en BD
   - Se puede reactivar si es necesario

---

## 📈 PRÓXIMOS PASOS (OPCIONAL)

### Mejoras Futuras Sugeridas

1. **Auditoría de Cambios**
   - Registrar quién cambió qué y cuándo
   - Log de asignación de roles
   - Historial de aprobaciones/rechazos

2. **Permisos Granulares**
   - Permisos por módulo (pedidos, productos, etc.)
   - Permisos de solo lectura vs escritura
   - Grupos de permisos personalizables

3. **Notificaciones en Tiempo Real**
   - WebSockets para notificaciones
   - Dashboard de actividad de usuarios
   - Alertas de seguridad

4. **Multi-tenancy**
   - Aislamiento por organización
   - Roles por organización
   - Datos segregados

---

## ✅ CHECKLIST DE VALIDACIÓN

Antes de considerar el sistema completo, verificar:

- [x] Migración 0006 aplicada correctamente
- [x] Test RBAC ejecutado sin errores
- [x] ADMIN no ve super_admin en lista
- [x] ADMIN no puede asignar role='super_admin'
- [x] USER no ve "Gestión de Usuarios"
- [x] Registro asigna role='user' automáticamente
- [x] Decoradores @admin_required funcionan
- [x] Validaciones backend bloquean acciones no autorizadas
- [x] Menú lateral muestra opciones según rol
- [x] Template filtra usuarios según permisos

---

## 📞 SOPORTE

Para dudas o problemas:
1. Revisar logs del servidor Django
2. Ejecutar `python test_rbac.py` para diagnosticar
3. Verificar estado de usuarios en BD
4. Consultar esta documentación

---

**Documento generado automáticamente por GitHub Copilot**  
**Fecha:** 3 de Febrero, 2026  
**Versión del Sistema:** 1.0  
**Estado:** ✅ PRODUCCIÓN
