from unittest.mock import patch

from django.test import SimpleTestCase

from apps.core.network_safety import validate_http_target


class NetworkSafetyTests(SimpleTestCase):
    def test_server_rejects_plain_http_when_https_required(self):
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            validate_http_target('http://203.0.113.10/api', require_https=True, resolve=False)

    def test_credentials_in_url_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Credentials'):
            validate_http_target('https://user:pass@example.com/api', resolve=False)

    def test_literal_loopback_is_blocked_for_server(self):
        with self.assertRaisesRegex(ValueError, 'Private/internal'):
            validate_http_target('https://127.0.0.1/api', require_https=True)

    def test_literal_private_ip_is_allowed_for_local(self):
        parsed = validate_http_target('http://192.168.1.50/api', allow_private=True)
        self.assertEqual(parsed.hostname, '192.168.1.50')

    @patch('apps.core.network_safety.socket.getaddrinfo')
    def test_hostname_resolving_to_private_ip_is_blocked(self, getaddrinfo):
        getaddrinfo.return_value=[(2,1,6,'',('10.0.0.7',443))]
        with self.assertRaisesRegex(ValueError, 'Private/internal'):
            validate_http_target('https://provider.example/api', require_https=True)

    @patch('apps.core.network_safety.socket.getaddrinfo')
    def test_hostname_resolving_to_public_ip_passes(self, getaddrinfo):
        getaddrinfo.return_value=[(2,1,6,'',('8.8.8.8',443))]
        parsed=validate_http_target('https://provider.example/api', require_https=True)
        self.assertEqual(parsed.hostname, 'provider.example')
