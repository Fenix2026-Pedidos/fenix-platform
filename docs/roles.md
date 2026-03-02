# Roles de Usuario en Plataforma Fenix

Este documento detalla los roles existentes en el sistema y los permisos que tienen asociados.

## 1. Super Admin (`super_admin`)
Es el rol de más alto nivel en la Plataforma Fenix. 
Tienen control total sobre todos los datos y la configuración del sistema.

**Permisos clave:**
- **Acceso al Backoffice (Staff):** Sí.
- **Superusuario (Superuser):** Sí.
- Acceso sin restricciones a todos los modelos de la base de datos (Catálogo, Pedidos, Usuarios, Configuración, etc.).
- Capacidad para crear, modificar, archivar y eliminar cualquier registro.
- Capacidad para gestionar a otros administradores y configurar aspectos críticos del sistema.

Ejemplo de usuario actual con este rol: `plataformafenix2026@gmail.com` (Vladimir Marfetan)

---

## 2. Administrador (`admin`)
Rol destinado a los responsables de gestionar las operaciones diarias (pedidos, catálogo), pero sin permiso para alterar la configuración principal del sistema o modificar a los super administradores.

**Permisos clave:**
- **Acceso al Backoffice (Staff):** Sí (otorgado explícitamente para gestionar la plataforma).
- **Superusuario (Superuser):** No.
- Acceso de vista y edición a modelos operacionales:
  - Catálogo (Productos, Categorías).
  - Pedidos.
  - Clientes/Usuarios básicos.
- No tienen acceso a opciones avanzadas de configuración o roles de superusuario.

Ejemplo de usuario actual con este rol: `distribuciones722@gmail.com` (Gilberto Giraldo)

---

## 3. Usuario / Cliente (`user`)
El rol estándar asignado a los clientes que navegan la parte pública de la plataforma Fenix y realizan pedidos.

**Permisos clave:**
- **Acceso al Backoffice (Staff):** No.
- **Superusuario (Superuser):** No.
- Acceso exclusivo al Frontend público e interfaz de Cliente (Dashboard de cliente, historial de pedidos propio, catálogo público).
- Restringidos estrictamente a la información de su propia cuenta de usuario y pedidos creados por ellos.

Ejemplo de usuarios actuales con este rol: 
- `vladimir.marfetanmorales@gmail.com`
- `vladimir.marfetan@gruposolutio.com`
- `vmarfetanmorales@gmail.com`

---

## Atributos de Estado (`status`)
Además del rol, cada usuario tiene un estado en la plataforma:
- **Activo (`active`):** El usuario puede iniciar sesión y operar en la plataforma.
- **Pendiente (`pending`):** Normalmente utilizado cuando el usuario se acaba de registrar y requiere aprobación de un administrador para poder operar y ver los precios finales del catálogo.
- **Archivado / Inactivo (`archived` / `inactive`):** El usuario ya no tiene acceso a la plataforma.

*Nota técnica para administradores:* 
Para conceder acceso al Backoffice a un usuario con rol `admin` o superior, es imprescindible que en la base de datos la propiedad `is_staff` de dicho usuario esté marcada como `True`.
