import json
from decimal import Decimal
from io import StringIO

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from accounts.middleware import CustomerOrganizationContextMiddleware
from accounts.models import (
    CustomerOrganization,
    CustomerOrganizationMembership,
    User,
)
from accounts.organizations import get_request_customer_organization
from orders.models import Order
from recurring.models import RecurringOrder


def create_client_user(email):
    return User.objects.create_user(
        email=email,
        password='Test-only-password-123!',
        full_name=email.split('@', 1)[0],
        status=User.STATUS_ACTIVE,
        email_verified=True,
        pending_approval=False,
        is_active=True,
    )


class CustomerOrganizationIsolationTests(TestCase):
    def setUp(self):
        self.owner = create_client_user('owner-a@example.test')
        self.colleague = create_client_user('member-a@example.test')
        self.outsider = create_client_user('owner-b@example.test')

        self.organization_a = self.owner.organization_membership.organization
        self.organization_b = self.outsider.organization_membership.organization

        colleague_membership = self.colleague.organization_membership
        colleague_membership.organization = self.organization_a
        colleague_membership.role = CustomerOrganizationMembership.ROLE_MEMBER
        colleague_membership.save(update_fields=['organization', 'role', 'updated_at'])

        self.order_a = Order.objects.create(
            customer=self.owner,
            status=Order.STATUS_NEW,
            total_amount=Decimal('100.00'),
        )
        self.order_b = Order.objects.create(
            customer=self.outsider,
            status=Order.STATUS_NEW,
            total_amount=Decimal('200.00'),
        )
        self.client_http = Client()

    def test_new_client_users_receive_separate_organizations(self):
        self.assertNotEqual(self.organization_a.pk, self.organization_b.pk)
        self.assertEqual(
            self.owner.organization_membership.role,
            CustomerOrganizationMembership.ROLE_OWNER,
        )

    def test_colleague_sees_orders_from_same_organization_only(self):
        self.client_http.force_login(self.colleague)

        response = self.client_http.get(reverse('orders:order_list'))

        self.assertEqual(response.status_code, 200)
        orders = list(response.context['orders'])
        self.assertIn(self.order_a, orders)
        self.assertNotIn(self.order_b, orders)

    def test_outsider_cannot_open_or_cancel_foreign_order(self):
        self.client_http.force_login(self.outsider)

        detail_response = self.client_http.get(
            reverse('orders:order_detail', args=[self.order_a.pk])
        )
        cancel_response = self.client_http.post(
            reverse('orders:order_cancel', args=[self.order_a.pk])
        )

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(cancel_response.status_code, 404)
        self.order_a.refresh_from_db()
        self.assertEqual(self.order_a.status, Order.STATUS_NEW)

    def test_order_rejects_customer_from_another_organization(self):
        order = Order(
            customer=self.owner,
            organization=self.organization_b,
            status=Order.STATUS_NEW,
        )

        with self.assertRaises(ValidationError):
            order.save()

    def test_suspended_organization_fails_closed(self):
        self.organization_a.status = CustomerOrganization.STATUS_SUSPENDED
        self.organization_a.save(update_fields=['status', 'updated_at'])
        self.client_http.force_login(self.owner)

        response = self.client_http.get(reverse('orders:order_list'))

        self.assertEqual(response.status_code, 403)

    def test_internal_order_update_remains_possible_after_suspension(self):
        self.organization_a.status = CustomerOrganization.STATUS_SUSPENDED
        self.organization_a.save(update_fields=['status', 'updated_at'])

        self.order_a.status = Order.STATUS_CANCELLED
        self.order_a.save(update_fields=['status', 'updated_at'])

        self.order_a.refresh_from_db()
        self.assertEqual(self.order_a.status, Order.STATUS_CANCELLED)

    def test_recurring_orders_are_scoped_to_organization(self):
        recurring = RecurringOrder.objects.create(
            customer=self.owner,
            is_active=True,
            frequency=RecurringOrder.FREQ_WEEKLY,
            start_date='2026-07-24',
        )
        self.assertEqual(recurring.organization_id, self.organization_a.pk)

        self.client_http.force_login(self.colleague)
        response = self.client_http.get(reverse('recurring:recurring_order_list'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(recurring, list(response.context['recurring_orders']))


class OrganizationScopingInfrastructureTests(TestCase):
    def setUp(self):
        self.owner = create_client_user('scope-owner@example.test')
        self.outsider = create_client_user('scope-outsider@example.test')
        self.organization = self.owner.organization_membership.organization
        self.outside_organization = (
            self.outsider.organization_membership.organization
        )
        self.order = Order.objects.create(
            customer=self.owner,
            status=Order.STATUS_NEW,
        )
        self.outside_order = Order.objects.create(
            customer=self.outsider,
            status=Order.STATUS_NEW,
        )

    def test_queryset_requires_explicit_organization(self):
        with self.assertRaises(PermissionDenied):
            Order.objects.for_organization(None)

        scoped_orders = list(Order.objects.for_organization(self.organization))
        self.assertEqual(scoped_orders, [self.order])

    def test_middleware_resolves_active_organization_once(self):
        request = RequestFactory().get('/orders/')
        request.user = self.owner
        middleware = CustomerOrganizationContextMiddleware(
            lambda current_request: HttpResponse('ok')
        )

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.customer_organization, self.organization)
        self.assertEqual(
            get_request_customer_organization(request),
            self.organization,
        )

    def test_middleware_marks_suspended_context_as_denied(self):
        self.organization.status = CustomerOrganization.STATUS_SUSPENDED
        self.organization.save(update_fields=['status', 'updated_at'])
        request = RequestFactory().get('/orders/')
        request.user = self.owner
        middleware = CustomerOrganizationContextMiddleware(
            lambda current_request: HttpResponse('ok')
        )

        middleware(request)

        self.assertTrue(request.customer_organization_access_denied)
        with self.assertRaises(PermissionDenied):
            get_request_customer_organization(request)

    def test_read_only_audit_reports_clean_and_inconsistent_states(self):
        clean_output = StringIO()
        call_command(
            'audit_organization_isolation',
            '--json',
            '--strict',
            stdout=clean_output,
        )
        clean_report = json.loads(clean_output.getvalue().splitlines()[0])
        self.assertEqual(clean_report['status'], 'ok')

        Order.objects.filter(pk=self.order.pk).update(
            organization=self.outside_organization
        )
        with self.assertRaises(CommandError):
            call_command(
                'audit_organization_isolation',
                '--strict',
                stdout=StringIO(),
            )
