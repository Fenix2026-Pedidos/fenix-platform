@echo off
REM Script para compilar traducciones añadiendo gettext al PATH
echo Añadiendo gettext al PATH...
set "PATH=%PATH%;C:\Program Files\gettext-iconv\bin"
cd /d "%~dp0"
echo.
echo Verificando gettext...
"C:\Program Files\gettext-iconv\bin\msgfmt.exe" --version
echo.
echo Compilando traducciones...
python manage.py compilemessages
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Traducciones compiladas correctamente!
    echo Recarga el servidor Django para ver los cambios.
) else (
    echo.
    echo [ERROR] Error al compilar traducciones
)
pause
