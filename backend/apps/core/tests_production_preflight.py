from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings


SAFE = dict(
    ENVIRONMENT="saas",
    DEBUG=False,
    SECRET_KEY="cafino-production-secret-key-that-is-long-and-random",
    DATABASES={"default": {"ENGINE": "django.db.backends.postgresql"}},
    SECURE_SSL_REDIRECT=True,
    SECURE_HSTS_SECONDS=3600,
    ALLOWED_HOSTS=["api.example.com"],
    CELERY_BROKER_URL="redis://127.0.0.1:6379/3",
    CORS_ALLOWED_ORIGINS=["https://app.example.com"],
    CSRF_TRUSTED_ORIGINS=["https://app.example.com"],
)


class ProductionPreflightTests(SimpleTestCase):
    def run_preflight(self):
        redis_client = Mock()
        redis_client.ping.return_value = True
        with (
            patch("apps.core.management.commands.production_preflight.connection.ensure_connection"),
            patch("apps.core.management.commands.production_preflight.redis.Redis.from_url", return_value=redis_client),
            patch("apps.core.management.commands.production_preflight.call_command"),
        ):
            output = StringIO()
            call_command("production_preflight", stdout=output)
            return output.getvalue()

    @override_settings(**SAFE)
    def test_safe_vps_profile_with_local_redis_passes(self):
        self.assertIn("Production preflight passed", self.run_preflight())

    @override_settings(**{**SAFE, "DEBUG": True})
    def test_debug_blocks_deployment(self):
        with self.assertRaises(CommandError):
            self.run_preflight()

    @override_settings(**{**SAFE, "SECRET_KEY": "too-short"})
    def test_weak_secret_blocks_deployment(self):
        with self.assertRaises(CommandError):
            self.run_preflight()

    @override_settings(**{**SAFE, "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}}})
    def test_sqlite_blocks_public_deployment(self):
        with self.assertRaises(CommandError):
            self.run_preflight()

    @override_settings(**{**SAFE, "ALLOWED_HOSTS": ["*"]})
    def test_wildcard_host_blocks_deployment(self):
        with self.assertRaises(CommandError):
            self.run_preflight()

    @override_settings(**{**SAFE, "CORS_ALLOWED_ORIGINS": ["http://app.example.com"]})
    def test_insecure_public_origin_blocks_deployment(self):
        with self.assertRaises(CommandError):
            self.run_preflight()
