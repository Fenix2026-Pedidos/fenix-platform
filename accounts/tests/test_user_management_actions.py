from unittest.mock import patch

from django.contrib import admin
from django.test import RequestFactory
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.admin import UserAdmin
from accounts.models import User
from accounts.permissions import can_assign_role, get_role_choices_for_user
from core.audit import AuditLog


def make_user(email, *, role=User.ROLE_USER, status=User.STATUS_ACTIVE):
    return User.objects.create_user(
        email=email,
        password='Test-only-password-123!',
        full_name=email.split('@', 1)[0],
        role=role,
        status=status,
        is_active=status != User.STATUS_DISABLED,
        pending_approval=status == User.STATUS_PENDING,
        email_verified=True,
    )


class UserManagementActionTests(TestCase):
    ajax_headers = {
        'HTTP_ACCEPT': 'application/json',
        'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
    }

    def setUp(self):
        self.super_admin = make_user(
            'super@example.test',
            role=User.ROLE_SUPER_ADMIN,
        )
        self.admin = make_user(
            'admin@example.test',
            role=User.ROLE_ADMIN,
        )
        self.client.force_login(self.super_admin)

    def test_dashboard_renders_accessible_action_buttons_and_real_script(self):
        target = make_user('cliente@example.test')

        response = self.client.get(reverse('accounts:user_approval_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Acciones de {target.display_name}')
        self.assertContains(response, 'aria-haspopup="menu"')
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, 'js/user_management_actions.js')

    def test_super_admin_role_is_never_exposed_or_assignable(self):
        target = make_user('role-target@example.test')

        dashboard = self.client.get(
            reverse('accounts:user_approval_dashboard')
        )
        edit_page = self.client.get(
            reverse('accounts:admin_edit_user', args=[target.pk])
        )

        self.assertNotContains(
            dashboard,
            '<option value="super_admin"',
            html=False,
        )
        self.assertNotContains(
            edit_page,
            '<option value="super_admin"',
            html=False,
        )
        self.assertNotIn(
            User.ROLE_SUPER_ADMIN,
            dict(get_role_choices_for_user(self.super_admin)),
        )
        self.assertFalse(
            can_assign_role(self.super_admin, User.ROLE_SUPER_ADMIN)
        )

    def test_super_admin_role_cannot_be_assigned_by_forged_request(self):
        target = make_user('forged-role@example.test')

        response = self.client.post(
            reverse('accounts:user_update', args=[target.pk]),
            {
                'first_name': 'Usuario',
                'last_name': 'Prueba',
                'company': 'Empresa',
                'role': User.ROLE_SUPER_ADMIN,
                'status': User.STATUS_ACTIVE,
                'email_verified': 'on',
            },
        )

        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertEqual(target.role, User.ROLE_USER)

    def test_django_admin_does_not_offer_super_admin_role(self):
        request = RequestFactory().get('/admin/accounts/user/add/')
        request.user = self.super_admin
        model_admin = UserAdmin(User, admin.site)

        role_field = model_admin.formfield_for_choice_field(
            User._meta.get_field('role'),
            request,
        )

        self.assertNotIn(
            User.ROLE_SUPER_ADMIN,
            dict(role_field.choices),
        )

    def test_disable_and_reactivate_user_return_json_and_are_audited(self):
        target = make_user('cliente@example.test')
        endpoint = reverse('accounts:user_status', args=[target.pk])

        disabled = self.client.post(
            endpoint,
            {'status': User.STATUS_DISABLED},
            **self.ajax_headers,
        )

        self.assertEqual(disabled.status_code, 200)
        target.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertEqual(target.status, User.STATUS_DISABLED)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_USER_DISABLED,
                object_id=target.pk,
            ).exists()
        )

        activated = self.client.post(
            endpoint,
            {'status': User.STATUS_ACTIVE},
            **self.ajax_headers,
        )
        self.assertEqual(activated.status_code, 200)
        target.refresh_from_db()
        self.assertTrue(target.is_active)
        self.assertEqual(target.status, User.STATUS_ACTIVE)

    def test_super_admin_cannot_disable_self(self):
        response = self.client.post(
            reverse('accounts:user_status', args=[self.super_admin.pk]),
            {'status': User.STATUS_DISABLED},
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 409)
        self.super_admin.refresh_from_db()
        self.assertTrue(self.super_admin.is_active)

    def test_last_super_admin_cannot_be_disabled_by_another_super_admin(self):
        second = make_user(
            'second-super@example.test',
            role=User.ROLE_SUPER_ADMIN,
        )
        self.client.force_login(second)

        response = self.client.post(
            reverse('accounts:user_status', args=[self.super_admin.pk]),
            {'status': User.STATUS_DISABLED},
            **self.ajax_headers,
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('accounts:user_status', args=[second.pk]),
            {'status': User.STATUS_DISABLED},
            **self.ajax_headers,
        )
        self.assertEqual(response.status_code, 409)

    def test_admin_cannot_modify_super_admin(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('accounts:user_status', args=[self.super_admin.pk]),
            {'status': User.STATUS_DISABLED},
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_approve_or_reject_pending_super_admin(self):
        pending_super = make_user(
            'pending-super@example.test',
            role=User.ROLE_SUPER_ADMIN,
            status=User.STATUS_PENDING,
        )
        self.client.force_login(self.admin)

        approve = self.client.post(
            reverse('accounts:approve_user', args=[pending_super.pk]),
            **self.ajax_headers,
        )
        reject = self.client.post(
            reverse('accounts:reject_user', args=[pending_super.pk]),
            **self.ajax_headers,
        )

        self.assertEqual(approve.status_code, 403)
        self.assertEqual(reject.status_code, 403)
        pending_super.refresh_from_db()
        self.assertEqual(pending_super.status, User.STATUS_PENDING)

    def test_regular_user_receives_json_403(self):
        regular = make_user('regular@example.test')
        target = make_user('other@example.test')
        self.client.force_login(regular)

        response = self.client.post(
            reverse('accounts:user_status', args=[target.pk]),
            {'status': User.STATUS_DISABLED},
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['ok'])

    @patch('django.contrib.auth.forms.PasswordResetForm.save')
    def test_password_reset_uses_official_flow_and_is_audited(self, save_mock):
        target = make_user('reset@example.test')

        response = self.client.post(
            reverse('accounts:admin_password_reset', args=[target.pk]),
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 200)
        save_mock.assert_called_once()
        self.assertTrue(
            AuditLog.objects.filter(
                action='password_reset_requested',
                object_id=target.pk,
            ).exists()
        )

    def test_password_reset_rejects_disabled_account(self):
        target = make_user(
            'disabled@example.test',
            status=User.STATUS_DISABLED,
        )

        response = self.client.post(
            reverse('accounts:admin_password_reset', args=[target.pk]),
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 409)

    @patch('accounts.utils.send_user_approved_email')
    def test_approve_pending_user_updates_counts_and_audit(self, _send_mock):
        pending = make_user(
            'pending@example.test',
            status=User.STATUS_PENDING,
        )

        response = self.client.post(
            reverse('accounts:approve_user', args=[pending.pk]),
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertEqual(pending.status, User.STATUS_ACTIVE)
        self.assertEqual(response.json()['counts']['pending'], 0)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_USER_APPROVED,
                object_id=pending.pk,
            ).exists()
        )

        duplicate = self.client.post(
            reverse('accounts:approve_user', args=[pending.pk]),
            **self.ajax_headers,
        )
        self.assertEqual(duplicate.status_code, 409)

    @patch('accounts.utils.send_user_rejected_email')
    def test_reject_pending_user_updates_counts_and_audit(self, _send_mock):
        pending = make_user(
            'reject@example.test',
            status=User.STATUS_PENDING,
        )

        response = self.client.post(
            reverse('accounts:reject_user', args=[pending.pk]),
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertEqual(pending.status, User.STATUS_REJECTED)
        self.assertEqual(response.json()['counts']['pending'], 0)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_USER_REJECTED,
                object_id=pending.pk,
            ).exists()
        )

    def test_pending_edit_persists_supported_fields(self):
        pending = make_user(
            'edit-pending@example.test',
            status=User.STATUS_PENDING,
        )

        response = self.client.post(
            reverse('accounts:update_pending_request'),
            {
                'user_id': pending.pk,
                'status': User.STATUS_PENDING,
                'role': User.ROLE_ADMIN,
                'full_name': 'Nombre actualizado',
                'company': 'Empresa actualizada',
                'email_verified': 'on',
            },
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertEqual(pending.full_name, 'Nombre actualizado')
        self.assertEqual(pending.company, 'Empresa actualizada')
        self.assertEqual(pending.role, User.ROLE_ADMIN)

    def test_pending_edit_cannot_bypass_approval_flow(self):
        pending = make_user(
            'cannot-bypass@example.test',
            status=User.STATUS_PENDING,
        )

        response = self.client.post(
            reverse('accounts:update_pending_request'),
            {
                'user_id': pending.pk,
                'status': User.STATUS_ACTIVE,
                'role': User.ROLE_USER,
                'full_name': pending.full_name,
                'company': pending.company,
            },
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 400)
        pending.refresh_from_db()
        self.assertEqual(pending.status, User.STATUS_PENDING)
