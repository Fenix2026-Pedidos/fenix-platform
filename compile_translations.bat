@echo off
REM Script para compilar traducciones añadiendo gettext al PATH
echo Añadiendo gettext al PATH...
set "PATH=%PATH%;C:\Program Files\gettext-iconv\bin;C:\Users\vladi\AppData\Local\Programs\gettext-iconv\bin"
cd /d "%~dp0"
echo.
echo Verificando gettext...
set "MSGFMT_PATH=C:\Program Files\gettext-iconv\bin\msgfmt.exe"
if not exist "%MSGFMT_PATH%" set "MSGFMT_PATH=C:\Users\vladi\AppData\Local\Programs\gettext-iconv\bin\msgfmt.exe"
"%MSGFMT_PATH%" --version
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
