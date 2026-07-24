import json

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from core.audit import AuditLog
from crm.models import CRMLead


def create_active_user(email, *, role=User.ROLE_USER, phone=''):
    return User.objects.create_user(
        email=email,
        password='Test-only-password-123!',
        full_name=email.split('@')[0],
        phone=phone,
        role=role,
        email_verified=True,
        pending_approval=False,
        status=User.STATUS_ACTIVE,
        is_active=True,
    )


class PersonalDataExportTests(TestCase):
    def setUp(self):
        self.user = create_active_user('empresa-a@example.test')
        self.other_user = create_active_user('empresa-b@example.test')
        CRMLead.objects.create(
            full_name='Contacto empresa A',
            email=self.user.email,
            phone='',
        )
        CRMLead.objects.create(
            full_name='Contacto empresa B',
            email=self.other_user.email,
            phone='',
        )
        self.client.force_login(self.user)

    def test_export_uses_real_profile_fields_and_returns_success(self):
        response = self.client.get(reverse('accounts:export_personal_data'))

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload['schema_version'], '1.0')
        self.assertEqual(payload['profile']['email'], self.user.email)
        self.assertIn('date_joined', payload['profile'])
        self.assertNotIn('created_at', payload['profile'])

    def test_export_never_matches_other_leads_by_blank_phone(self):
        response = self.client.get(reverse('accounts:export_personal_data'))

        payload = json.loads(response.content)
        exported_emails = {lead['email'] for lead in payload['crm']}
        self.assertEqual(exported_emails, {self.user.email})
        self.assertNotContains(response, self.other_user.email)

    def test_export_is_audited(self):
        self.client.get(reverse('accounts:export_personal_data'))

        self.assertTrue(
            AuditLog.objects.filter(
                user=self.user,
                action=AuditLog.ACTION_PERSONAL_DATA_EXPORTED,
            ).exists()
        )


@override_settings(ALLOW_HARD_DELETE=False)
class ReversibleAdministrativeRemovalTests(TestCase):
    def setUp(self):
        self.admin = create_active_user(
            'admin@example.test',
            role=User.ROLE_ADMIN,
        )
        self.client.force_login(self.admin)

    def test_user_delete_endpoint_disables_instead_of_deleting(self):
        target = create_active_user('cliente@example.test')

        response = self.client.post(
            reverse('accounts:user_delete', args=[target.pk])
        )

        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertEqual(target.status, User.STATUS_DISABLED)
        self.assertFalse(target.is_active)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_USER_DISABLED,
                object_id=target.pk,
            ).exists()
        )

    def test_crm_delete_endpoint_archives_instead_of_deleting(self):
        lead = CRMLead.objects.create(
            full_name='Lead de prueba',
            email='lead@example.test',
        )

        response = self.client.post(
            reverse('crm:delete_lead', args=[lead.uuid])
        )

        self.assertEqual(response.status_code, 200)
        lead.refresh_from_db()
        self.assertEqual(lead.validation_status, CRMLead.VALIDATION_DESCARTADO)
        self.assertEqual(lead.lead_status, CRMLead.STATUS_PERDIDO)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_CRM_LEAD_ARCHIVED,
                object_id=lead.pk,
            ).exists()
        )
