# FENIX - Plataforma de Gestión de Pedidos

Plataforma B2B para gestión operativa de pedidos con soporte multi-idioma (ES/ZH).

## 🚀 Guía Rápida

Consulte la documentación principal en la carpeta `docs/`:

1.  **[Configuración Inicial](docs/security.md#despliegue)**: Pasos para poner en marcha el proyecto.
2.  **[Sistema de Seguridad](docs/security.md)**: Detalles sobre el sistema de 2 pasos (Email + Admin).
3.  **[Roles y Permisos (RBAC)](docs/rbac.md)**: Gestión de niveles de acceso.
4.  **[Idiomas y Traducción](docs/i18n.md)**: Funcionamiento del soporte multi-idioma.
5.  **[Referencia de API](docs/api.md)**: Endpoints y ejemplos de uso.

## 📁 Estructura del Proyecto

El proyecto está organizado en módulos (Django Apps) especializados:

-   **[accounts/](accounts/README.md)**: Usuarios, autenticación y seguridad.
-   **[catalog/](catalog/README.md)**: Productos, categorías y traducción automática.
-   **[orders/](orders/README.md)**: Ciclo de vida del pedido y carrito.
-   **[recurring/](recurring/README.md)**: Pedidos programados y suscripciones.
-   **[notifications/](notifications/README.md)**: Sistema de notificaciones por email.
-   **[core/](core/README.md)**: Configuración global y búsquedas.

## 🛠️ Tecnologías

-   **Backend**: Django 6.0
-   **Base de Datos**: PostgreSQL (Supabase) / SQLite (Dev)
-   **Despliegue**: Google Cloud App Engine / Render

---

Para más detalles, consulte la **[Preguntas Frecuentes (FAQ)](docs/faq.md)** o las **[Guías de Usuario](docs/guides/)**.
