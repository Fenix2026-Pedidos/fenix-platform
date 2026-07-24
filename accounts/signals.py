"""Creación segura del contexto empresarial de nuevas cuentas cliente."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from accounts.organizations import ensure_customer_organization


@receiver(post_save, sender=User, dispatch_uid='accounts.ensure_customer_organization')
def provision_customer_organization(sender, instance, raw=False, **kwargs):
    if raw:
        return
    ensure_customer_organization(instance)
