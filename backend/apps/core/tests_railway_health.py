from django.test import SimpleTestCase, override_settings


class RailwayHealthcheckTests(SimpleTestCase):
    @override_settings(
        ALLOWED_HOSTS=['healthcheck.railway.app'],
        SECURE_SSL_REDIRECT=True,
        SECURE_REDIRECT_EXEMPT=[r'^api/v1/health/$'],
    )
    def test_railway_healthcheck_is_accepted_without_https_redirect(self):
        response = self.client.get(
            '/api/v1/health/',
            HTTP_HOST='healthcheck.railway.app',
            secure=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'service': 'cafino-backend'})
