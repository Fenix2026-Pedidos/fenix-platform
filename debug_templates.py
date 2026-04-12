import os
import django
from django.conf import settings
from django.template.loader import get_template, render_to_string

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fenix.settings')
django.setup()

def debug_templates():
    print("--- DIAGNÓSTICO DE PLANTILLAS ---")
    print(f"BASE_DIR: {settings.BASE_DIR}")
    
    template_name = 'components/sidebar.html'
    try:
        template = get_template(template_name)
        print(f"Plantilla encontrada: {template_name}")
        print(f"Origen (archivo): {template.origin.name}")
        
        # Verificar contenido
        content = open(template.origin.name, 'r', encoding='utf-8').read()
        if 'sidebarCartBadge' in content:
            print("VERIFICACIÓN: El archivo contiene 'sidebarCartBadge' (mi cambio previo).")
        else:
            print("ALERTA: El archivo NO contiene 'sidebarCartBadge'.")
            
    except Exception as e:
        print(f"ERROR al buscar la plantilla: {e}")

if __name__ == '__main__':
    debug_templates()
