import json
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AILead


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AssistantSecurityTests(TestCase):
    payload = {
        'name': 'Persona de prueba',
        'email': 'persona@example.com',
        'phone_prefix': '+34',
        'phone_number': '612345678',
        'privacy_accepted': True,
    }

    @patch('ai_assistant.views.secrets.randbelow', return_value=123456)
    def test_otp_is_hashed_and_never_returned(self, mocked_random):
        response = self.client.post(
            reverse('ai_assistant:capture_lead'),
            data=json.dumps(self.payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('fallback_otp', response.json())
        lead = AILead.objects.get(email=self.payload['email'])
        self.assertNotEqual(lead.otp_code, '123456')
        self.assertTrue(check_password('123456', lead.otp_code))
        self.assertIsNotNone(lead.privacy_accepted_at)

    @patch('ai_assistant.views.secrets.randbelow', return_value=123456)
    @patch('ai_assistant.views.AIService.generate_response', return_value='Respuesta segura')
    def test_verified_lead_uses_server_session(self, mocked_ai, mocked_random):
        self.client.post(
            reverse('ai_assistant:capture_lead'),
            data=json.dumps(self.payload),
            content_type='application/json',
        )
        verified = self.client.post(
            reverse('ai_assistant:verify_otp'),
            data=json.dumps({'email': self.payload['email'], 'otp': '123456'}),
            content_type='application/json',
        )
        self.assertEqual(verified.status_code, 200)
        chat = self.client.post(
            reverse('ai_assistant:chat'),
            data=json.dumps({'message': 'Hola', 'email': 'otra-persona@example.com'}),
            content_type='application/json',
        )
        self.assertEqual(chat.status_code, 200)
        self.assertEqual(chat.json()['response'], 'Respuesta segura')

