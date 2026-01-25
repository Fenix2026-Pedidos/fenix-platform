#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Configurar codificación UTF-8 para evitar errores de Unicode
if sys.platform == 'win32':
    import locale
    if sys.getdefaultencoding() != 'utf-8':
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        # Forzar UTF-8 en Windows
        if hasattr(sys, 'setdefaultencoding'):
            sys.setdefaultencoding('utf-8')


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fenix.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
