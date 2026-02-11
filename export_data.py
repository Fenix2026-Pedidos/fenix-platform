"""Export all data from SQLite to JSON with proper UTF-8 encoding."""
import os, sys, io

# Force UTF-8 everywhere
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fenix.settings')

import django
django.setup()

from django.core.management import call_command

EXCLUDES = [
    'contenttypes',
    'auth.Permission',
    'admin.logentry',
    'sessions.session',
]

print("Exportando datos de SQLite...")
try:
    call_command(
        'dumpdata',
        '--natural-foreign',
        '--natural-primary',
        '--indent=2',
        *[f'--exclude={e}' for e in EXCLUDES],
        output='full_dump.json',
    )
    size = os.path.getsize('full_dump.json')
    print(f"OK - full_dump.json creado ({size:,} bytes)")
except Exception as e:
    print(f"Error: {e}")
    # Fallback: export app by app
    print("Intentando exportar app por app...")
    apps_to_export = [
        'accounts', 'catalog', 'orders', 'recurring',
        'notifications', 'core', 'organizations', 'auth.Group',
    ]
    all_data = []
    import json
    for app in apps_to_export:
        try:
            out = io.StringIO()
            call_command(
                'dumpdata', app,
                '--natural-foreign', '--natural-primary',
                '--indent=2',
                stdout=out,
            )
            data = json.loads(out.getvalue())
            all_data.extend(data)
            print(f"  {app}: {len(data)} objetos")
        except Exception as ex:
            print(f"  {app}: SKIP ({ex})")

    with open('full_dump.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    size = os.path.getsize('full_dump.json')
    print(f"OK - full_dump.json creado ({size:,} bytes)")
