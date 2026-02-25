# Configuración de i18n en Fenix

## Estado Actual

El selector de idiomas está completamente configurado y funcional. Django i18n está activado con soporte para:
- Español (es) - idioma por defecto
- Inglés (en)
- Chino Simplificado (zh-hans)

## Configuración Implementada

### 1. Settings (fenix/settings.py)
- ✅ `USE_I18N = True`
- ✅ `LocaleMiddleware` en `MIDDLEWARE` (posición correcta: después de SessionMiddleware)
- ✅ `LANGUAGES` definido con es, en, zh-hans
- ✅ `LOCALE_PATHS` configurado
- ✅ `LANGUAGE_COOKIE_NAME`, `LANGUAGE_COOKIE_AGE`, etc. configurados

### 2. URLs (fenix/urls.py)
- ✅ Endpoint: `/i18n/setlang/` usando `set_language` de Django
- ✅ Nombre de URL: `set_language`

### 3. Templates
- ✅ `templates/components/topbar.html`: Selector con `{% get_current_language %}` y `{% get_available_languages %}`
- ✅ `templates/base.html`: Selector para usuarios no autenticados
- ✅ Ambos usan `request.get_full_path` para el parámetro `next`

### 4. Archivos de Traducción
- ✅ Creados archivos `.po` básicos en:
  - `locale/es/LC_MESSAGES/django.po`
  - `locale/en/LC_MESSAGES/django.po`
  - `locale/zh_Hans/LC_MESSAGES/django.po`

## Cómo Funciona

1. **Usuario selecciona idioma**: El formulario POST envía a `/i18n/setlang/`
2. **Django procesa**: `set_language` guarda el idioma en:
   - Cookie: `django_language`
   - Sesión: `django_language`
3. **LocaleMiddleware**: En cada request, lee el idioma de cookie/sesión y lo activa
4. **Templates**: Usan `{% trans %}` para mostrar textos traducidos
5. **Redirección**: Django redirige a la URL en `next` (la página actual)

## Compilar Traducciones (Opcional)

Para compilar los archivos `.po` a `.mo` (requiere gettext):

```bash
python manage.py compilemessages
```

**Nota**: Si no tienes gettext instalado, el cambio de idioma seguirá funcionando, pero los textos no se traducirán hasta que compiles los mensajes.

### Instalar gettext en Windows:
1. Descargar: https://mlocati.github.io/articles/gettext-iconv-windows.html
2. Añadir a PATH
3. Ejecutar `python manage.py compilemessages`

## Probar el Funcionamiento

1. **Abrir el catálogo**: `http://127.0.0.1:8000/`
2. **Seleccionar "中文"** en el selector de idioma
3. **Verificar**:
   - La página se recarga
   - El selector muestra "中文" como seleccionado
   - Los textos marcados con `{% trans %}` deberían cambiar (si están compilados)
4. **Navegar a otra página**: El idioma persiste
5. **Recargar la página**: El idioma persiste (cookie)
6. **Cerrar y abrir navegador**: El idioma persiste (cookie de 1 año)

## Textos Traducidos Actualmente

Los siguientes textos tienen traducciones en los archivos `.po`:
- Catálogo / Catalog / 产品目录
- Mis Pedidos / My Orders / 我的订单
- Carrito / Cart / 购物车
- Aprobación de Usuarios / User Approval / 用户审批
- Administración / Administration / 管理
- Catálogo de Productos / Product Catalog / 产品目录
- Buscar productos... / Search products... / 搜索产品...
- Añadir / Add / 添加
- En carrito: / In cart: / 购物车中：
- Mi Perfil / My Profile / 我的资料
- Cerrar Sesión / Log Out / 退出登录
- Iniciar Sesión / Log In / 登录
- Registrarse / Sign Up / 注册

## Añadir Más Traducciones

1. Marcar texto en template: `{% trans "Texto a traducir" %}`
2. Ejecutar: `python manage.py makemessages -l es -l en -l zh_Hans`
3. Editar archivos `.po` en `locale/*/LC_MESSAGES/django.po`
4. Compilar: `python manage.py compilemessages`
5. Recargar servidor

## Troubleshooting

- **El idioma no cambia**: Verificar que `LocaleMiddleware` esté en `MIDDLEWARE`
- **No persiste**: Verificar cookies del navegador
- **Textos no se traducen**: Ejecutar `compilemessages` o verificar que los textos estén marcados con `{% trans %}`
