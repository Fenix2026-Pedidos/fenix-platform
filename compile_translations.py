import polib
import os

def compile_translations():
    po_file_path = r'c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix\locale\zh_Hans\LC_MESSAGES\django.po'
    mo_file_path = r'c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix\locale\zh_Hans\LC_MESSAGES\django.mo'
    
    if not os.path.exists(po_file_path):
        print(f"Error: {po_file_path} not found.")
        return

    try:
        po = polib.pofile(po_file_path, encoding='utf-8')
        po.save_as_mofile(mo_file_path)
        print(f"Successfully compiled {po_file_path} to {mo_file_path}")
    except Exception as e:
        print(f"Error compiling translations: {e}")

if __name__ == "__main__":
    compile_translations()
