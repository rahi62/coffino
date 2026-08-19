from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings


SAFE = dict(
    ENVIRONMENT="saas",
    DEBUG=False,
    SECRET_KEY="cafino-production-secret-key-that-is-not-a-placeholder",
    DATABASES={"default": {"ENGINE": "django.db.backends.postgresql"}},
    SECURE_SSL_REDIRECT=True,
    SECURE_HSTS_SECONDS=3600,
    ALLOWED_HOSTS=["api.example.com", "healthcheck.railway.app"],
    ON_RAILWAY=True,
    CELERY_BROKER_URL="redis://redis.railway.internal:6379/0",
    CORS_ALLOWED_ORIGINS=["https://app.example.com"],
    CSRF_TRUSTED_ORIGINS=["https://app.example.com"],
)


class RailwayPreflightTests(SimpleTestCase):
    @override_settings(**SAFE)
    def test_safe_public_profile_passes(self):
        output = StringIO()
        call_command("railway_preflight", stdout=output)
        self.assertIn("Railway preflight passed", output.getvalue())

    @override_settings(**{**SAFE, "DEBUG": True})
    def test_debug_blocks_deployment(self):
        with self.assertRaises(CommandError):
            call_command("railway_preflight")

    @override_settings(**{**SAFE, "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}}})
    def test_sqlite_blocks_public_deployment(self):
        with self.assertRaises(CommandError):
            call_command("railway_preflight")

    @override_settings(**{**SAFE, "ALLOWED_HOSTS": ["*"]})
    def test_wildcard_host_blocks_deployment(self):
        with self.assertRaises(CommandError):
            call_command("railway_preflight")

    @override_settings(**{**SAFE, "CELERY_BROKER_URL": "redis://127.0.0.1:6379/0"})
    def test_local_redis_blocks_deployment(self):
        with self.assertRaises(CommandError):
            call_command("railway_preflight")

    @override_settings(**{**SAFE, "CORS_ALLOWED_ORIGINS": ["http://app.example.com"]})
    def test_insecure_public_origin_blocks_deployment(self):
        with self.assertRaises(CommandError):
            call_command("railway_preflight")
