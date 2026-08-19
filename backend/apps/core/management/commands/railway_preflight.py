from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def _host(value):
    try:
        return (urlparse(str(value or "")).hostname or "").lower()
    except Exception:
        return ""


class Command(BaseCommand):
    help = "Fail fast when Cafino public deployment settings are unsafe or incomplete for Railway."

    def handle(self, *args, **options):
        errors = []
        environment = str(getattr(settings, "ENVIRONMENT", "")).lower()
        allowed_hosts = list(getattr(settings, "ALLOWED_HOSTS", []) or [])
        database = dict(getattr(settings, "DATABASES", {}).get("default", {}) or {})
        broker = str(getattr(settings, "CELERY_BROKER_URL", "") or "")
        cors = list(getattr(settings, "CORS_ALLOWED_ORIGINS", []) or [])
        csrf = list(getattr(settings, "CSRF_TRUSTED_ORIGINS", []) or [])

        if environment not in {"saas", "dedicated"}:
            errors.append("CAF_INO_ENV must be saas or dedicated for a public Railway deployment.")
        if bool(getattr(settings, "DEBUG", False)):
            errors.append("DJANGO_DEBUG must be 0 for Railway production.")
        if str(getattr(settings, "SECRET_KEY", "")) == "dev-secret-change-me":
            errors.append("DJANGO_SECRET_KEY is still the development placeholder.")

        engine = str(database.get("ENGINE") or "")
        if "postgresql" not in engine:
            errors.append("Railway public deployment must use PostgreSQL; SQLite is not allowed.")

        if not bool(getattr(settings, "SECURE_SSL_REDIRECT", False)):
            errors.append("DJANGO_SECURE_SSL_REDIRECT must be enabled for public deployment.")
        if int(getattr(settings, "SECURE_HSTS_SECONDS", 0) or 0) <= 0:
            errors.append("DJANGO_HSTS_SECONDS must be greater than zero for public deployment.")
        if "*" in allowed_hosts:
            errors.append("DJANGO_ALLOWED_HOSTS must not contain wildcard '*'.")
        if bool(getattr(settings, "ON_RAILWAY", False)) and "healthcheck.railway.app" not in allowed_hosts:
            errors.append("healthcheck.railway.app must be accepted while running on Railway.")

        parsed_broker = urlparse(broker)
        if parsed_broker.scheme not in {"redis", "rediss"}:
            errors.append("REDIS_URL/CELERY_BROKER_URL must use redis:// or rediss://.")
        if _host(broker) in {"", "localhost", "127.0.0.1", "::1"}:
            errors.append("Celery broker must point to the Railway Redis service, not localhost.")

        for origin in [*cors, *csrf]:
            if origin and not str(origin).startswith("https://"):
                errors.append(f"Public CORS/CSRF origin must use HTTPS: {origin}")

        if errors:
            for message in errors:
                self.stderr.write(self.style.ERROR(f"- {message}"))
            raise CommandError(f"Railway preflight failed with {len(errors)} blocking issue(s).")

        self.stdout.write(
            self.style.SUCCESS(
                "Railway preflight passed: public security, PostgreSQL, Redis, hosts and origins are safe enough to migrate."
            )
        )
