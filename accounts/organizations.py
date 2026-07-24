"""Resolución segura del contexto de empresa cliente."""

from django.core.exceptions import PermissionDenied
from django.db import transaction

from accounts.models import CustomerOrganization, CustomerOrganizationMembership


def _default_organization_name(user):
    return (
        (user.company or '').strip()
        or (user.full_name or '').strip()
        or user.email.split('@', 1)[0]
    )[:200]


@transaction.atomic
def ensure_customer_organization(user):
    """Crea una empresa aislada para un cliente que todavía no la tiene."""
    if user.is_staff or user.is_superuser or user.role != user.ROLE_USER:
        return None

    membership = (
        CustomerOrganizationMembership.objects
        .select_related('organization')
        .filter(user=user)
        .first()
    )
    if membership:
        return membership.organization

    organization = CustomerOrganization.objects.create(
        name=_default_organization_name(user),
        legal_name=(user.company or '').strip()[:250],
        tax_id=(user.vat_number or '').strip()[:30],
    )
    CustomerOrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=CustomerOrganizationMembership.ROLE_OWNER,
        status=CustomerOrganizationMembership.STATUS_ACTIVE,
    )
    return organization


def get_user_customer_membership(user):
    """Devuelve la pertenencia asignada, incluso si está suspendida."""
    if not user.is_authenticated:
        raise PermissionDenied('Se requiere autenticación.')

    try:
        membership = (
            CustomerOrganizationMembership.objects
            .select_related('organization')
            .get(user=user)
        )
    except CustomerOrganizationMembership.DoesNotExist as exc:
        raise PermissionDenied(
            'La cuenta no está asociada a una empresa cliente.'
        ) from exc

    return membership


def get_user_customer_organization(user):
    """Devuelve la empresa activa del usuario o deniega el acceso."""
    membership = get_user_customer_membership(user)

    if (
        membership.status != CustomerOrganizationMembership.STATUS_ACTIVE
        or membership.organization.status != CustomerOrganization.STATUS_ACTIVE
    ):
        raise PermissionDenied('La pertenencia a la empresa no está activa.')

    return membership.organization


def get_request_customer_organization(request):
    """Usa el contexto resuelto por middleware y falla cerrado si fue denegado."""
    if getattr(request, 'customer_organization_access_denied', False):
        raise PermissionDenied('El contexto de empresa cliente no está activo.')

    organization = getattr(request, 'customer_organization', None)
    if organization is not None:
        return organization

    return get_user_customer_organization(request.user)
