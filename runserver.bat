@echo off
REM Script para ejecutar Django con codificación UTF-8 configurada
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"
python manage.py runserver --noreload
pause
