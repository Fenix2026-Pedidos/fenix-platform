#!/usr/bin/env python
"""
Script para compilar archivos .po a .mo usando polib (biblioteca Python pura).
"""
import os
from pathlib import Path

try:
    import polib
except ImportError:
    print("Instalando polib...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'polib'])
    import polib

BASE_DIR = Path(__file__).resolve().parent
LOCALE_DIR = BASE_DIR / 'locale'

def compile_po_to_mo(po_file, mo_file):
    """Compila un archivo .po a .mo usando polib."""
    try:
        po = polib.pofile(str(po_file))
        po.save_as_mofile(str(mo_file))
        print(f"[OK] Compilado: {po_file.name} -> {mo_file.name}")
        return True
    except Exception as e:
        print(f"[ERROR] Error compilando {po_file.name}: {e}")
        return False

def main():
    """Compila todos los archivos .po en locale/"""
    if not LOCALE_DIR.exists():
        print(f"Directorio locale/ no encontrado: {LOCALE_DIR}")
        return
    
    compiled = 0
    for lang_dir in LOCALE_DIR.iterdir():
        if not lang_dir.is_dir():
            continue
        
        po_file = lang_dir / 'LC_MESSAGES' / 'django.po'
        mo_file = lang_dir / 'LC_MESSAGES' / 'django.mo'
        
        if po_file.exists():
            if compile_po_to_mo(po_file, mo_file):
                compiled += 1
    
    print(f"\n[OK] Compilados {compiled} archivos de traduccion")
    print("Recarga el servidor Django para aplicar las traducciones.")

if __name__ == '__main__':
    main()
