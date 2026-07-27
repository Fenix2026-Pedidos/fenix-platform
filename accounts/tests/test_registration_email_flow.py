from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from django.core.mail import EmailMessage
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import EmailVerificationToken, User
from accounts.utils import send_verification_email
from core.email_backends import ResendDeliveryError, ResendEmailBackend


class RegistrationEmailFlowTests(TestCase):
    def registration_data(self, email):
        return {
            "full_name": "Usuario de prueba",
            "email": email,
            "company": "Empresa de prueba",
            "password1": "Test-Password-2026!",
            "password2": "Test-Password-2026!",
        }

    @patch("accounts.utils.send_new_user_admin_notification")
    @patch("core.crm_services.CRMService.sync_lead")
    @patch("accounts.views.send_verification_email")
    def test_registration_redirects_to_verification_after_confirmed_send(
        self, send_verification, sync_lead, notify_admin
    ):
        response = self.client.post(
            reverse("accounts:register"),
            self.registration_data("new-user@example.com"),
        )

        self.assertRedirects(response, reverse("accounts:email_verification"))
        self.assertTrue(User.objects.filter(email="new-user@example.com").exists())
        self.assertEqual(
            self.client.session["unverified_user_email"],
            "new-user@example.com",
        )
        send_verification.assert_called_once()
        sync_lead.assert_called_once()
        notify_admin.assert_called_once()

    @patch("accounts.utils.send_new_user_admin_notification")
    @patch("core.crm_services.CRMService.sync_lead")
    @patch(
        "accounts.views.send_verification_email",
        side_effect=ResendDeliveryError("provider rejected"),
    )
    def test_registration_reports_delivery_failure_without_false_success(
        self, send_verification, sync_lead, notify_admin
    ):
        response = self.client.post(
            reverse("accounts:register"),
            self.registration_data("failed-send@example.com"),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.url_name, "email_verification")
        self.assertContains(response, "no hemos podido enviar el email")
        user = User.objects.get(email="failed-send@example.com")
        self.assertEqual(user.status, User.STATUS_PENDING)
        self.assertFalse(user.email_verified)

    @patch(
        "accounts.views.send_verification_email",
        side_effect=ResendDeliveryError("provider rejected"),
    )
    def test_resend_endpoint_returns_service_unavailable_on_delivery_failure(
        self, send_verification
    ):
        User.objects.create_user(
            email="resend@example.com",
            password="Test-Password-2026!",
            full_name="Usuario reenvío",
            company="Empresa",
            email_verified=False,
            status=User.STATUS_PENDING,
        )

        response = self.client.post(
            reverse("accounts:resend_confirmation"),
            {"email": "resend@example.com"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["success"])

    @patch("django.core.mail.EmailMultiAlternatives.send", return_value=0)
    def test_failed_verification_send_removes_unused_token(self, send):
        user = User.objects.create_user(
            email="token-cleanup@example.com",
            password="Test-Password-2026!",
            full_name="Usuario token",
            company="Empresa",
        )

        with self.assertRaises(RuntimeError):
            send_verification_email(
                user,
                "https://www.fenixdelamancha.es/accounts/verify-email/",
            )

        self.assertFalse(EmailVerificationToken.objects.filter(user=user).exists())


class ResendBackendTests(TestCase):
    @override_settings(
        RESEND_API_KEY="test-key",
        RESEND_DEFAULT_FROM="Fenix <noreply@fenixdelamancha.es>",
    )
    @patch("core.email_backends.urllib.request.urlopen")
    def test_http_error_is_propagated_with_provider_reason(self, urlopen):
        urlopen.side_effect = HTTPError(
            url="https://api.resend.com/emails",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=BytesIO(
                b'{"message":"The fenixdelamancha.es domain is not verified"}'
            ),
        )
        backend = ResendEmailBackend(fail_silently=False)
        message = EmailMessage(
            subject="Prueba",
            body="Prueba",
            from_email="Fenix <noreply@fenixdelamancha.es>",
            to=["recipient@example.com"],
        )

        with self.assertRaisesRegex(ResendDeliveryError, "domain is not verified"):
            backend.send_messages([message])
