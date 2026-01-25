# Instalar gettext en Windows para compilar traducciones

## Opción 1: Usando el instalador oficial (Recomendado)

1. **Descargar gettext para Windows:**
   - Visita: https://mlocati.github.io/articles/gettext-iconv-windows.html
   - Descarga la versión más reciente (gettext-0.21.1 o superior)
   - O directamente: https://github.com/mlocati/gettext-iconv-windows/releases

2. **Instalar:**
   - Ejecuta el instalador `.exe`
   - Durante la instalación, **marca la opción "Add to PATH"** o añádelo manualmente después

3. **Verificar instalación:**
   ```bash
   msgfmt --version
   ```

4. **Compilar traducciones:**
   ```bash
   python manage.py compilemessages
   ```

## Opción 2: Usando Chocolatey (si tienes Chocolatey instalado)

```bash
choco install gettext
```

Luego:
```bash
python manage.py compilemessages
```

## Opción 3: Usando MSYS2 (si ya lo tienes)

```bash
pacman -S gettext
```

## Verificar que funciona

Después de instalar gettext, ejecuta:

```bash
cd "c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix"
python manage.py compilemessages
```

Deberías ver algo como:
```
processing file django.po in locale\es\LC_MESSAGES
processing file django.po in locale\zh_Hans\LC_MESSAGES
```

## Solución de problemas

### Error: "Can't find msgfmt"
- Asegúrate de que gettext esté en el PATH
- Reinicia la terminal después de instalar
- Verifica con: `where msgfmt`

### Error: "UnicodeDecodeError"
- Los archivos `.po` deben estar en UTF-8
- Ya están configurados correctamente con `charset=UTF-8` en el header

### Después de compilar
- Recarga el servidor Django: `python manage.py runserver`
- Selecciona "中文" en el selector de idioma
- Los textos deberían aparecer en chino
