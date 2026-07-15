import os

from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured


def _fernet():
    key = os.getenv('TOTP_ENCRYPTION_KEY', '').encode('ascii')
    if not key:
        raise ImproperlyConfigured('TOTP_ENCRYPTION_KEY es obligatoria para usar 2FA.')
    try:
        return Fernet(key)
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured('TOTP_ENCRYPTION_KEY no es una clave Fernet válida.') from exc


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode('utf-8')).decode('ascii')


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode('ascii')).decode('utf-8')
    except InvalidToken as exc:
        raise ImproperlyConfigured('No se pudo descifrar el secreto 2FA.') from exc

