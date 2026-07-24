"""Auditoría read-only del aislamiento entre empresas cliente."""

import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, F, Q

from accounts.models import (
    CustomerOrganization,
    CustomerOrganizationMembership,
    User,
)
from orders.models import Order
from recurring.models import RecurringOrder


def build_isolation_report():
    client_users = User.objects.filter(
        role=User.ROLE_USER,
        is_staff=False,
        is_superuser=False,
    )
    active_membership_filter = Q(
        memberships__status=CustomerOrganizationMembership.STATUS_ACTIVE
    )

    report = {
        'client_users_without_membership': client_users.filter(
            organization_membership__isnull=True
        ).count(),
        'internal_users_with_membership': (
            User.objects
            .filter(organization_membership__isnull=False)
            .filter(
                ~Q(role=User.ROLE_USER)
                | Q(is_staff=True)
                | Q(is_superuser=True)
            )
            .count()
        ),
        'organizations_without_active_members': (
            CustomerOrganization.objects
            .annotate(
                active_members=Count(
                    'memberships',
                    filter=active_membership_filter,
                )
            )
            .filter(active_members=0)
            .count()
        ),
        'orders_without_organization': Order.objects.filter(
            organization__isnull=True
        ).count(),
        'orders_without_customer_membership': Order.objects.filter(
            customer__organization_membership__isnull=True
        ).count(),
        'orders_with_mismatched_organization': (
            Order.objects
            .filter(customer__organization_membership__isnull=False)
            .exclude(
                organization_id=F(
                    'customer__organization_membership__organization_id'
                )
            )
            .count()
        ),
        'recurring_orders_without_organization': RecurringOrder.objects.filter(
            organization__isnull=True
        ).count(),
        'recurring_orders_without_customer_membership': (
            RecurringOrder.objects.filter(
                customer__organization_membership__isnull=True
            ).count()
        ),
        'recurring_orders_with_mismatched_organization': (
            RecurringOrder.objects
            .filter(customer__organization_membership__isnull=False)
            .exclude(
                organization_id=F(
                    'customer__organization_membership__organization_id'
                )
            )
            .count()
        ),
    }
    critical_keys = (
        'client_users_without_membership',
        'orders_without_organization',
        'orders_without_customer_membership',
        'orders_with_mismatched_organization',
        'recurring_orders_without_organization',
        'recurring_orders_without_customer_membership',
        'recurring_orders_with_mismatched_organization',
    )
    report['critical_total'] = sum(report[key] for key in critical_keys)
    report['status'] = 'ok' if report['critical_total'] == 0 else 'failed'
    return report


class Command(BaseCommand):
    help = (
        'Audita el aislamiento por empresa sin modificar datos. '
        'Use --strict para fallar si existen inconsistencias críticas.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true', dest='as_json')
        parser.add_argument('--strict', action='store_true')

    def handle(self, *args, **options):
        report = build_isolation_report()
        if options['as_json']:
            self.stdout.write(json.dumps(report, sort_keys=True))
        else:
            for key, value in report.items():
                self.stdout.write(f'{key}: {value}')

        if options['strict'] and report['critical_total']:
            raise CommandError(
                'La auditoría detectó inconsistencias críticas de aislamiento.'
            )

        if not report['critical_total']:
            self.stdout.write(self.style.SUCCESS('Aislamiento coherente.'))
