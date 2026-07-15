from django.conf import settings
from django.core.files.storage import FileSystemStorage


def private_media_storage():
    """Storage exclusivo para documentos y ficheros personales."""
    if settings.DEBUG:
        return FileSystemStorage(location=settings.BASE_DIR / 'private_media')

    from storages.backends.gcloud import GoogleCloudStorage
    return GoogleCloudStorage(
        bucket_name=settings.GS_PRIVATE_BUCKET_NAME,
        default_acl=None,
        querystring_auth=True,
        expiration=300,
        file_overwrite=False,
    )


# Nombre estable utilizado por las migraciones y modelos de pedidos.
private_order_storage = private_media_storage
