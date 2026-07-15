"""Carga secretos exclusivamente desde el proyecto GCP activo de Fenix."""

from __future__ import annotations

import logging
import os

from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

SECRET_ENV_MAP = {
    "fenix-django-secret-key": "SECRET_KEY",
    "fenix-db-name": "DB_NAME",
    "fenix-db-user": "DB_USER",
    "fenix-db-password": "DB_PASSWORD",
    "fenix-db-host": "DB_HOST",
    "fenix-db-port": "DB_PORT",
    "fenix-email-host-user": "EMAIL_HOST_USER",
    "fenix-email-host-password": "EMAIL_HOST_PASSWORD",
    "fenix-resend-api-key": "RESEND_API_KEY",
    "fenix-whatsapp-access-token": "WHATSAPP_ACCESS_TOKEN",
    "fenix-whatsapp-webhook-verify-token": "WHATSAPP_WEBHOOK_VERIFY_TOKEN",
    "fenix-whatsapp-app-secret": "WHATSAPP_APP_SECRET",
    "fenix-google-api-key": "GOOGLE_API_KEY",
    "fenix-google-sheets-webhook-url": "GOOGLE_SHEETS_WEBHOOK_URL",
    "fenix-totp-encryption-key": "TOTP_ENCRYPTION_KEY",
}


def load_project_secrets() -> None:
    if os.getenv("LOAD_GCP_SECRETS", "false").lower() not in {"1", "true", "yes"}:
        return

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCLOUD_PROJECT")
    if not project_id:
        raise ImproperlyConfigured(
            "LOAD_GCP_SECRETS está activo pero no existe un proyecto GCP activo."
        )

    try:
        from google.cloud import secretmanager
    except ImportError as exc:
        raise ImproperlyConfigured("Falta google-cloud-secret-manager.") from exc

    client = secretmanager.SecretManagerServiceClient()
    unavailable: list[str] = []
    for secret_name, env_name in SECRET_ENV_MAP.items():
        if os.getenv(env_name):
            continue
        resource = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        try:
            response = client.access_secret_version(request={"name": resource})
        except Exception:
            unavailable.append(secret_name)
            continue
        os.environ[env_name] = response.payload.data.decode("utf-8")

    required = {"SECRET_KEY", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST"}
    unresolved = sorted(name for name in required if not os.getenv(name))
    if unresolved:
        raise ImproperlyConfigured(
            "Faltan secretos obligatorios de Fenix: " + ", ".join(unresolved)
        )
    if unavailable:
        logger.warning("Secretos opcionales de Fenix no disponibles: %s", ", ".join(unavailable))
