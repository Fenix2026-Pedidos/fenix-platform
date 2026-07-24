"""QuerySets reutilizables para datos propiedad de empresas cliente."""

from django.core.exceptions import PermissionDenied
from django.db import models


class CustomerOrganizationScopedQuerySet(models.QuerySet):
    """Exige un ámbito empresarial explícito y nunca devuelve todo por defecto."""

    def for_organization(self, organization):
        organization_id = getattr(organization, 'pk', organization)
        if not organization_id:
            raise PermissionDenied('Falta el contexto de empresa cliente.')
        return self.filter(organization_id=organization_id)

    def for_customer_user(self, user):
        from accounts.organizations import get_user_customer_organization

        return self.for_organization(get_user_customer_organization(user))
