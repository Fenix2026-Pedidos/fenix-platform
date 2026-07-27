import csv
import io

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from core.audit import AuditLog
from crm.models import CRMLead


class CRMLeadListToolsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='crm-admin@example.test',
            password='Test-only-password-123!',
            full_name='CRM Admin',
            role=User.ROLE_ADMIN,
            email_verified=True,
            pending_approval=False,
            status=User.STATUS_ACTIVE,
            is_active=True,
        )
        self.client.force_login(self.admin)
        self.converted = CRMLead.objects.create(
            full_name='=Contacto convertido',
            company_name='Empresa Uno',
            email='convertido@example.test',
            lead_status=CRMLead.STATUS_CONVERTIDO,
        )
        CRMLead.objects.create(
            full_name='Contacto pendiente',
            company_name='Empresa Dos',
            email='pendiente@example.test',
            lead_status=CRMLead.STATUS_PENDIENTE,
        )

    def test_list_removes_duplicate_status_chips_and_exposes_real_tools(self):
        response = self.client.get(reverse('crm:leads_list'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'status-chips-container')
        self.assertContains(response, 'Exportar vista actual (CSV)')
        self.assertContains(response, 'id="columns-menu"')
        self.assertContains(response, 'data-column="col-zone"')
        self.assertContains(response, 'onclick="toggleColumnButton(this)"')

    def test_csv_export_respects_current_filters_and_is_audited(self):
        response = self.client.get(
            reverse('crm:export_leads_csv'),
            {'status': CRMLead.STATUS_CONVERTIDO},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8-sig')
        rows = list(csv.reader(io.StringIO(content)))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], self.converted.serial_id)
        self.assertEqual(rows[1][1], "'=Contacto convertido")
        self.assertNotIn('pendiente@example.test', content)
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.admin,
                action=AuditLog.ACTION_PERSONAL_DATA_EXPORTED,
                object_type='CRMLead',
            ).exists()
        )

    def test_csv_export_requires_crm_access(self):
        user = User.objects.create_user(
            email='cliente@example.test',
            password='Test-only-password-123!',
            full_name='Cliente',
            role=User.ROLE_USER,
            email_verified=True,
            pending_approval=False,
            status=User.STATUS_ACTIVE,
            is_active=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('crm:export_leads_csv'))

        self.assertEqual(response.status_code, 403)
