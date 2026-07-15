"""Falla CI si un archivo versionado parece contener secretos o volcados."""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parent.parent
FORBIDDEN_NAMES = re.compile(
    r'(^|/)(\.env($|\.)|.*credentials.*|.*dump.*\.json$|.*\.sqlite3($|\.)|.*\.backup$)',
    re.IGNORECASE,
)
SECRET_ASSIGNMENT = re.compile(
    r'^\s*(DB_PASSWORD|SECRET_KEY|EMAIL_HOST_PASSWORD|WHATSAPP_ACCESS_TOKEN|'
    r'WHATSAPP_WEBHOOK_VERIFY_TOKEN|WHATSAPP_APP_SECRET|GOOGLE_API_KEY)\s*:\s*["\']?\S+',
    re.MULTILINE,
)


def main() -> int:
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
    failures: list[str] = []
    for relative in tracked:
        normalized = relative.replace('\\', '/')
        path = ROOT / relative
        if not path.exists():
            # Permite ejecutar la puerta localmente antes de confirmar borrados.
            continue
        if normalized == '.env.example':
            continue
        if FORBIDDEN_NAMES.search(normalized):
            failures.append(f'archivo prohibido versionado: {normalized}')
            continue
        if path.suffix.lower() not in {'.py', '.yaml', '.yml', '.json', '.md', '.txt', '.ps1', '.bat'}:
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        if SECRET_ASSIGNMENT.search(content) and path.name not in {'.env.example'}:
            failures.append(f'posible secreto incrustado: {normalized}')
    if failures:
        print('\n'.join(failures))
        return 1
    print('Security gate OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
