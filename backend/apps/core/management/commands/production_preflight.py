from urllib.parse import urlparse

import redis
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


PLACEHOLDER_SECRETS = {
    "",
    "dev-secret-change-me",
    "change-this-in-production",
    "ci-only-secret",
}


class Command(BaseCommand):
    help = "Fail fast when a Cafino public production environment is unsafe or incomplete."

    def handle(self, *args, **options):
        errors = []
        environment = str(getattr(settings, "ENVIRONMENT", "") or "").lower()
        secret_key = str(getattr(settings, "SECRET_KEY", "") or "")
        allowed_hosts = list(getattr(settings, "ALLOWED_HOSTS", []) or [])
        database = dict(getattr(settings, "DATABASES", {}).get("default", {}) or {})
        broker = str(getattr(settings, "CELERY_BROKER_URL", "") or "")
        cors = list(getattr(settings, "CORS_ALLOWED_ORIGINS", []) or [])
        csrf = list(getattr(settings, "CSRF_TRUSTED_ORIGINS", []) or [])

        if environment not in {"saas", "dedicated"}:
            errors.append("CAF_INO_ENV must be saas or dedicated for a public production deployment.")
        if bool(getattr(settings, "DEBUG", False)):
            errors.append("DJANGO_DEBUG must be 0 for production.")
        if (
            secret_key in PLACEHOLDER_SECRETS
            or secret_key.startswith("django-insecure-")
            or len(secret_key) < 32
        ):
            errors.append("DJANGO_SECRET_KEY must be a strong, non-placeholder value of at least 32 characters.")

        engine = str(database.get("ENGINE") or "")
        if "postgresql" not in engine:
            errors.append("Public production must use PostgreSQL; SQLite is not allowed.")

        if not bool(getattr(settings, "SECURE_SSL_REDIRECT", False)):
            errors.append("DJANGO_SECURE_SSL_REDIRECT must be enabled for public production.")
        if int(getattr(settings, "SECURE_HSTS_SECONDS", 0) or 0) <= 0:
            errors.append("DJANGO_HSTS_SECONDS must be greater than zero for public production.")
        if not allowed_hosts or "*" in allowed_hosts:
            errors.append("DJANGO_ALLOWED_HOSTS must contain explicit hosts and no wildcard '*'.")

        parsed_broker = urlparse(broker)
        if parsed_broker.scheme not in {"redis", "rediss"}:
            errors.append("REDIS_URL/CELERY_BROKER_URL must use redis:// or rediss://.")

        if not cors:
            errors.append("CORS_ALLOWED_ORIGINS must contain at least one HTTPS origin.")
        if not csrf:
            errors.append("CSRF_TRUSTED_ORIGINS must contain at least one HTTPS origin.")
        for origin in [*cors, *csrf]:
            if origin and not str(origin).startswith("https://"):
                errors.append(f"Public CORS/CSRF origin must use HTTPS: {origin}")

        if "postgresql" in engine:
            try:
                connection.ensure_connection()
            except Exception as exc:
                errors.append(f"PostgreSQL connection failed: {exc.__class__.__name__}")

        if parsed_broker.scheme in {"redis", "rediss"}:
            try:
                redis.Redis.from_url(broker, socket_connect_timeout=3, socket_timeout=3).ping()
            except Exception as exc:
                errors.append(f"Redis connection failed: {exc.__class__.__name__}")

        try:
            call_command("makemigrations", check=True, dry_run=True, verbosity=0)
        except Exception as exc:
            errors.append(f"Migration consistency check failed: {exc.__class__.__name__}")

        if errors:
            for message in errors:
                self.stderr.write(self.style.ERROR(f"- {message}"))
            raise CommandError(f"Production preflight failed with {len(errors)} blocking issue(s).")

        self.stdout.write(
            self.style.SUCCESS(
                "Production preflight passed: SaaS mode, security, PostgreSQL, Redis, hosts, origins, and migrations are valid."
            )
        )
