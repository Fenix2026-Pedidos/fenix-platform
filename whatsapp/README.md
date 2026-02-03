# Integración WhatsApp Business Cloud API

Esta app permite a los usuarios de la zona pública de Fenix contactar por WhatsApp a través de un botón flotante (FAB) que envía mensajes usando la API oficial de WhatsApp Business Cloud (Meta).

## Configuración

### Variables de Entorno

Agrega las siguientes variables a tu archivo `.env`:

```env
# WhatsApp Business Cloud API - Configuración
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id_aqui
WHATSAPP_BUSINESS_ACCOUNT_ID=tu_business_account_id_aqui  # Opcional, para referencia
WHATSAPP_ACCESS_TOKEN=tu_access_token_aqui
DEFAULT_WHATSAPP_TARGET=346XXXXXXXX  # Número destino en formato internacional sin +
```

### Cómo obtener las credenciales

1. **Crear una cuenta de Meta Business**:
   - Ve a https://business.facebook.com/
   - Crea o selecciona una cuenta de negocio

2. **Configurar WhatsApp Business API**:
   - Ve a https://developers.facebook.com/
   - Crea una nueva app o usa una existente
   - Agrega el producto "WhatsApp"
   - Sigue el proceso de configuración

3. **Obtener Phone Number ID**:
   - En el dashboard de Meta for Developers
   - Ve a WhatsApp > API Setup
   - Copia el "Phone number ID"

4. **Obtener Access Token**:
   - En el mismo panel de API Setup
   - Genera un token temporal o permanente
   - **IMPORTANTE**: Guarda el token de forma segura

5. **Número de destino**:
   - El número debe estar verificado en tu cuenta de WhatsApp Business
   - Formato: código de país + número (sin + ni espacios)
   - Ejemplo: `34612345678` para España

## Instalación

1. La app ya está registrada en `settings.py`:
   ```python
   INSTALLED_APPS = [
       ...
       'whatsapp',
   ]
   ```

2. Las URLs ya están configuradas en `fenix/urls.py`

3. El frontend ya está integrado en `templates/base.html` (solo para usuarios no autenticados)

## Uso

### Para usuarios públicos

1. Los usuarios verán un botón flotante verde de WhatsApp en la esquina inferior derecha
2. Al hacer clic, se abre un modal con un formulario
3. El usuario completa:
   - Nombre
   - Mensaje
4. Al enviar, el mensaje se envía a través de WhatsApp Business API

### Formato del mensaje recibido

El mensaje que recibirás en WhatsApp tendrá este formato:

```
Nuevo contacto Fenix:

Nombre: [Nombre del usuario]
Página: [URL de la página desde donde se envió]

Mensaje:
[Mensaje del usuario]
```

## Endpoint API

### POST `/api/whatsapp/send/`

**Headers:**
- `Content-Type: application/json`
- `X-CSRFToken: [token]` (si CSRF está habilitado)

**Body:**
```json
{
  "name": "Juan Pérez",
  "message": "Hola, me interesa el producto X",
  "page_url": "https://fenix.com/catalog/product/123"
}
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "message": "Mensaje enviado correctamente"
}
```

**Respuesta de error:**
```json
{
  "success": false,
  "error": "Descripción del error"
}
```

## Seguridad

- ✅ Tokens almacenados en variables de entorno (nunca en código)
- ✅ Timeout de 10 segundos en requests
- ✅ Manejo completo de errores y logging
- ✅ Validación de campos en backend y frontend
- ✅ CSRF protection (aunque el endpoint usa `@csrf_exempt`, el frontend envía el token)

## Estructura de Archivos

```
whatsapp/
├── __init__.py
├── services.py          # Lógica de envío a WhatsApp API
├── views.py             # Endpoint API
├── urls.py              # URLs de la app
└── README.md            # Este archivo

templates/public/partials/
└── whatsapp_fab.html    # Template del botón y modal

static/
├── js/
│   └── whatsapp.js      # JavaScript del FAB y formulario
└── css/
    └── whatsapp.css     # Estilos del FAB y modal
```

## Troubleshooting

### El botón no aparece

- Verifica que estés en la zona pública (no autenticado)
- Revisa la consola del navegador por errores JavaScript
- Verifica que los archivos estáticos se estén sirviendo correctamente

### Error al enviar mensaje

1. **Verifica las variables de entorno**:
   ```python
   # En Django shell: python manage.py shell
   import os
   print(os.getenv('WHATSAPP_PHONE_NUMBER_ID'))
   print(os.getenv('WHATSAPP_ACCESS_TOKEN'))
   print(os.getenv('DEFAULT_WHATSAPP_TARGET'))
   ```

2. **Revisa los logs del servidor**:
   - Los errores se registran en el log de Django
   - Busca mensajes con "whatsapp" o "WhatsApp"

3. **Verifica el token**:
   - El token puede haber expirado (si es temporal)
   - Regenera el token en Meta for Developers

4. **Verifica el número destino**:
   - Debe estar en formato internacional sin +
   - Debe estar verificado en tu cuenta de WhatsApp Business

### Error 401 (Unauthorized)

- El token de acceso es inválido o ha expirado
- Regenera el token en Meta for Developers

### Error 400 (Bad Request)

- Verifica que el `PHONE_NUMBER_ID` sea correcto
- Verifica que el número destino esté en el formato correcto
- Revisa los logs para más detalles

## Próximos pasos (opcional)

- [ ] Implementar webhook para recibir mensajes entrantes
- [ ] Guardar mensajes en base de datos (modelo `WhatsAppLead`)
- [ ] Rate limiting por IP
- [ ] Campo honeypot anti-spam
- [ ] Notificaciones por email cuando llega un mensaje

## Referencias

- [WhatsApp Business Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Meta for Developers](https://developers.facebook.com/)
