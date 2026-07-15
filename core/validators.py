from pathlib import Path

from django.core.exceptions import ValidationError


MAX_PRIVATE_DOCUMENT_SIZE = 10 * 1024 * 1024
ALLOWED_PRIVATE_DOCUMENT_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.docx', '.xlsx'}


def validate_private_document(upload):
    if upload.size > MAX_PRIVATE_DOCUMENT_SIZE:
        raise ValidationError('El archivo no puede superar 10 MB.')
    extension = Path(upload.name).suffix.lower()
    if extension not in ALLOWED_PRIVATE_DOCUMENT_EXTENSIONS:
        raise ValidationError('Formato no permitido. Usa PDF, PNG, JPG, DOCX o XLSX.')

    position = upload.tell()
    header = upload.read(8)
    upload.seek(position)
    signatures = {
        '.pdf': (b'%PDF-',),
        '.png': (b'\x89PNG\r\n\x1a\n',),
        '.jpg': (b'\xff\xd8\xff',),
        '.jpeg': (b'\xff\xd8\xff',),
        '.docx': (b'PK\x03\x04',),
        '.xlsx': (b'PK\x03\x04',),
    }
    if not any(header.startswith(signature) for signature in signatures[extension]):
        raise ValidationError('El contenido del archivo no coincide con su extensión.')

