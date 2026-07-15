"""Limitación global de frecuencia para endpoints públicos."""

from __future__ import annotations

import hashlib
from datetime import timedelta

from django.db import transaction
from django.utils import timezone


def client_ip(request) -> str:
    return request.META.get('HTTP_X_APPENGINE_USER_IP') or request.META.get('REMOTE_ADDR') or 'unknown'


def rate_limited(request, scope: str, limit: int, window: int, identity: str = '') -> bool:
    # Import tardío para evitar cargar modelos durante la inicialización de apps.
    from core.models import RateLimitBucket

    raw_identity = identity.strip().lower() or client_ip(request)
    digest = hashlib.sha256(raw_identity.encode('utf-8')).hexdigest()
    bucket_number = int(timezone.now().timestamp()) // window
    key = f'{scope}:{bucket_number}:{digest}'
    expires_at = timezone.now() + timedelta(seconds=window)

    with transaction.atomic():
        bucket, created = RateLimitBucket.objects.select_for_update().get_or_create(
            key=key,
            defaults={'count': 1, 'expires_at': expires_at},
        )
        if created:
            return False
        bucket.count += 1
        bucket.save(update_fields=['count'])
        return bucket.count > limit
