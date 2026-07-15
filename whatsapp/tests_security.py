import hashlib
import hmac
import json
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse


class WhatsAppSecurityTests(TestCase):
    def test_unsigned_webhook_is_rejected(self):
        response = self.client.post(
            reverse('whatsapp:webhook'),
            data=json.dumps({'entry': []}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_signed_webhook_is_accepted(self):
        body = json.dumps({'entry': []}).encode('utf-8')
        secret = 'test-only-secret'
        signature = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        with patch.dict('os.environ', {'WHATSAPP_APP_SECRET': secret}):
            response = self.client.post(
                reverse('whatsapp:webhook'),
                data=body,
                content_type='application/json',
                HTTP_X_HUB_SIGNATURE_256=signature,
            )
        self.assertEqual(response.status_code, 200)

    def test_public_send_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse('whatsapp:send_message'),
            data=json.dumps({'name': 'Test', 'message': 'Hola'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
