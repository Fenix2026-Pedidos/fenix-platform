import ast
import pathlib
import sys


errors = []
files = list(pathlib.Path('.').rglob('*.py'))
for path in files:
    if any(part in {'.venv', 'venv'} for part in path.parts):
        continue
    try:
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    except Exception as exc:
        errors.append(f'{path}: {exc}')

if errors:
    print('\n'.join(errors))
    sys.exit(1)
print(f'AST OK: {len(files)} files')
