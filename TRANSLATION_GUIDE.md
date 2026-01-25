# Guía de Traducción - FENIX

## 📋 Resumen

FENIX implementa **dos sistemas de traducción diferentes**:

### 1. 🌐 Selector de Idioma en el Header (UI/Interfaz)
**¿Qué traduce?**
- Menús, botones, etiquetas, mensajes de la interfaz
- Textos del sistema (ej: "Catálogo", "Mis Pedidos", "Cerrar Sesión")
- Mensajes de error y notificaciones

**¿Dónde está?**
- Selector en el **topbar** (header) con opciones: 🇪🇸 ES / 🇨🇳 中文
- Visible para todos los usuarios (autenticados y no autenticados)

**¿Cómo funciona?**
- Usa Django i18n (`{% trans %}`)
- Cambia el idioma de la sesión actual
- Los textos se traducen automáticamente según el idioma seleccionado

### 2. 🤖 Traducción Automática de Productos (Contenido)
**¿Qué traduce?**
- Nombres de productos (`name_es` → `name_zh_hans`)
- Descripciones de productos (`description_es` → `description_zh_hans`)

**¿Dónde está?**
- En el **Admin de Django** al editar un producto
- Botón: "🌐 Traducir automáticamente (ES → 中文)"

**¿Cómo funciona?**
- Usa la librería `deep-translator` con Google Translate (gratuito, sin API key)
- Traduce automáticamente de español a chino simplificado
- También traduce automáticamente al guardar un nuevo producto (si solo tiene campos en español)

## 🎯 ¿Cuál usar?

### Para Usuarios Finales (Clientes):
✅ **Selector de idioma en el header**
- Cambian el idioma de la interfaz (ES/中文)
- Ven los productos en su idioma preferido según `user.language` o el selector

### Para Managers/Admins:
✅ **Traducción automática en el admin**
- Añaden productos solo en español
- Hacen clic en "Traducir automáticamente"
- Revisan y ajustan las traducciones si es necesario
- Guardan el producto

## 📝 Flujo Recomendado

1. **Manager añade producto:**
   - Completa `name_es` y `description_es`
   - (Opcional) Completa `name_zh_hans` y `description_zh_hans` manualmente
   - O hace clic en "Traducir automáticamente" para traducir

2. **Cliente ve el producto:**
   - Si su idioma es ES → ve `name_es` y `description_es`
   - Si su idioma es zh-hans → ve `name_zh_hans` y `description_zh_hans`
   - Puede cambiar el idioma de la UI con el selector del header

## ⚙️ Configuración

### Instalar dependencia:
```bash
pip install deep-translator
```

### Variables de entorno (opcional):
No se requiere API key. La librería `deep-translator` usa Google Translate de forma gratuita (con limitaciones de uso).

## 🔧 Personalización

### Cambiar el idioma por defecto:
- En `PlatformSettings` (Admin → Configuración de la Plataforma)
- Campo: `default_language`

### Ajustar traducciones automáticas:
- Editar `catalog/utils.py` → función `translate_text()`
- Cambiar `source_lang` o `target_lang` si es necesario

## ⚠️ Notas Importantes

1. **Traducción automática no es perfecta**: Siempre revisa las traducciones, especialmente para términos técnicos o nombres propios.

2. **Límites de Google Translate**: La librería gratuita tiene límites de uso. Para producción con alto volumen, considera usar una API oficial.

3. **Dos sistemas independientes**:
   - El selector de idioma NO traduce productos automáticamente
   - La traducción automática solo funciona en el admin

4. **Prioridad de idioma para productos**:
   - Si el usuario tiene `user.language = 'zh-hans'` → ve productos en chino
   - Si el usuario tiene `user.language = 'es'` → ve productos en español
   - El selector del header cambia la UI, pero los productos se muestran según `user.language`
