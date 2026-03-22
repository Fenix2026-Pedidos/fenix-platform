# Traducción Automática ES → 中文 - Estado y Solución

## ✅ Lo que YA está implementado

1. **Librería instalada**: `deep-translator>=1.11.4` en `requirements.txt`
2. **Código de traducción**: `catalog/utils.py` con funciones `translate_text()` y `translate_product_fields()`
3. **Botón en Admin**: Botón "🌐 Traducir automáticamente (ES → 中文)" en el admin de productos
4. **Vista de traducción**: Endpoint `/admin/catalog/product/<id>/translate/` para traducir vía AJAX
5. **Traducción automática al guardar**: Si creas un producto nuevo solo con `name_es`, se traduce automáticamente a `name_zh_hans`

## 🔧 Problema encontrado y SOLUCIONADO

### Error anterior:
El código intentaba usar `'zh'` como código de idioma, pero `deep-translator` requiere `'zh-CN'` para chino simplificado.

### Solución aplicada:
✅ Corregido `catalog/utils.py` para usar directamente `'zh-CN'` sin conversión.

## 📋 Checklist de verificación

Para que funcione completamente, verifica:

### 1. Dependencia instalada
```bash
pip install deep-translator
```

### 2. Acceso a Internet
- `deep-translator` necesita conexión a Internet para acceder a Google Translate
- Si estás detrás de un proxy corporativo, puede fallar
- Verifica que tu conexión funcione

### 3. Cómo usar la traducción automática

#### Opción A: Botón en el Admin (recomendado)
1. Ve a Admin → Productos → Editar un producto existente
2. Completa los campos `name_es` y `description_es`
3. Haz clic en el botón "🌐 Traducir automáticamente (ES → 中文)"
4. Los campos `name_zh_hans` y `description_zh_hans` se llenarán automáticamente
5. Revisa las traducciones y guarda

#### Opción B: Traducción automática al crear
1. Ve a Admin → Productos → Añadir producto
2. Completa solo `name_es` (y opcionalmente `description_es`)
3. Deja `name_zh_hans` y `description_zh_hans` vacíos
4. Guarda el producto
5. **Automáticamente** se traducirán los campos al chino

## ⚠️ Posibles problemas y soluciones

### Problema 1: "Error al traducir texto"
**Causa**: Sin conexión a Internet o proxy bloqueando
**Solución**: 
- Verifica tu conexión a Internet
- Si usas proxy, configura las variables de entorno:
  ```bash
  set HTTP_PROXY=http://proxy:puerto
  set HTTPS_PROXY=http://proxy:puerto
  ```

### Problema 2: "LanguageNotSupportedException"
**Causa**: Código de idioma incorrecto (ya corregido)
**Solución**: ✅ Ya está solucionado usando `'zh-CN'`

### Problema 3: El botón no aparece
**Causa**: El producto debe estar guardado primero
**Solución**: 
- Guarda el producto primero (aunque esté vacío)
- Luego edítalo y verás el botón

### Problema 4: Traducción devuelve texto original
**Causa**: Error en la traducción (red, límites de Google, etc.)
**Solución**: 
- Revisa los logs de Django para ver el error específico
- Intenta de nuevo (puede ser un problema temporal de red)

## 🧪 Prueba manual

Para probar que funciona, ejecuta en Python:

```python
from catalog.utils import translate_text

# Probar traducción
resultado = translate_text("Jamón Ibérico", 'es', 'zh-CN')
print(f"Traducción: {resultado}")
```

Debería imprimir algo como: `Traducción: 伊比利亚火腿`

## 📝 Notas importantes

1. **Google Translate gratuito tiene límites**: 
   - No abuses de la traducción automática
   - Para producción con alto volumen, considera una API oficial

2. **Las traducciones no son perfectas**:
   - Siempre revisa las traducciones automáticas
   - Ajusta manualmente si es necesario

3. **Funciona solo en el Admin**:
   - La traducción automática solo está disponible en Django Admin
   - Los usuarios finales ven los productos según su idioma configurado

## ✅ Estado actual

- ✅ Código corregido (`catalog/utils.py`)
- ✅ Botón funcional en Admin
- ✅ Traducción automática al guardar
- ⚠️ Requiere conexión a Internet
- ⚠️ Requiere `deep-translator` instalado
