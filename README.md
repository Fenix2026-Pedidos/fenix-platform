# FENIX - Plataforma de Gestión de Pedidos

Plataforma B2B single-tenant para gestión operativa de pedidos con soporte multi-idioma (ES/中文).

## Características MVP

- ✅ Single-tenant (sin multi-organización)
- ✅ Catálogo tipo ecommerce
- ✅ Gestión completa del ciclo de vida del pedido
- ✅ Pedidos recurrentes/programados
- ✅ Backoffice operativo para managers
- ✅ Gestión básica de stock
- ✅ Notificaciones automáticas por email
- ✅ Soporte multilenguaje (Español / Chino Simplificado)
- ✅ Arquitectura preparada para IA

## Tecnologías

- **Backend:** Django 6.0
- **Base de datos:** PostgreSQL (Supabase)
- **Python:** 3.11+

## Configuración Inicial

### 1. Instalar dependencias

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configurar Supabase

1. Crea un archivo `.env` en la raíz del proyecto (copia `.env.example`)
2. Completa las credenciales de tu proyecto Supabase (y opcionalmente `EMAIL_*` para notificaciones por correo):

```env
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=db.tu-proyecto.supabase.co
DB_PORT=5432
SECRET_KEY=tu-secret-key
DEBUG=True
```

### 3. Ejecutar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Crear superusuario

```bash
python manage.py createsuperuser
```

### 5. Ejecutar servidor

```bash
python manage.py runserver
```

### 6. (Opcional) Compilar traducciones

Si se añaden cadenas traducibles en `locale/`:

```bash
python manage.py compilemessages
```

## Estructura del Proyecto

- `accounts/` - Modelo de usuarios y autenticación
- `catalog/` - Productos y catálogo
- `orders/` - Pedidos y gestión de estados
- `recurring/` - Pedidos recurrentes
- `notifications/` - Sistema de notificaciones
- `core/` - Configuración global de plataforma

## Roles del Sistema

- **Super Admin:** Control total de la plataforma
- **Manager:** Backoffice operativo, gestión de pedidos y productos
- **Cliente:** Ver catálogo, crear pedidos, ver seguimiento

## Estados de Pedido

1. **Nuevo** - Pedido creado
2. **Confirmado** - Validado por manager
3. **Preparando** - En preparación (se descuenta stock)
4. **En reparto** - Enviado
5. **Entregado** - Recibido y validado
6. **Cancelado** - Cancelado por manager

## Idiomas Soportados

- Español (es)
- Chino Simplificado (zh-hans)

Prioridad de idioma:
1. `user.language`
2. `platform.default_language`
3. `es` (fallback)

## Notas Importantes

- El cliente **NO ve stock** (solo managers)
- El stock se descuenta cuando el pedido pasa a **PREPARANDO**
- Todas las funcionalidades deben tener soporte ES/CN
- Single-tenant: todos los usuarios comparten el mismo catálogo
