from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from core.middleware import SecurityHeadersMiddleware
from core.rate_limit import rate_limited


class SecurityControlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_rate_limit_is_enforced(self):
        request = self.factory.get('/', REMOTE_ADDR='192.0.2.10')
        self.assertFalse(rate_limited(request, 'test', 2, 60))
        self.assertFalse(rate_limited(request, 'test', 2, 60))
        self.assertTrue(rate_limited(request, 'test', 2, 60))

    def test_security_headers_are_added(self):
        middleware = SecurityHeadersMiddleware(lambda request: HttpResponse('ok'))
        response = middleware(self.factory.get('/'))
        self.assertIn('Content-Security-Policy-Report-Only', response)
        self.assertEqual(response['X-Permitted-Cross-Domain-Policies'], 'none')

