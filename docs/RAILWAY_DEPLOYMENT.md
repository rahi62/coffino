> **SUPERSEDED FOR CURRENT PRODUCTION:** Cafino production has moved to Coolify. Keep this document only as historical Railway guidance. Use `docs/COOLIFY_DEPLOYMENT.md` for the active release process.

# Cafino Web/SaaS on Railway

Cafino is deployed from this monorepo as separate Railway services. Keep PostgreSQL and Redis private; only Backend and Frontend need public domains.

## Services

Create these services from the same GitHub repository:

| Service | Root directory | Config file | Public | Purpose |
|---|---|---|---|---|
| `cafino-backend` | `/backend` | `/backend/railway.toml` | Yes | Django/DRF API |
| `cafino-frontend` | `/frontend` | `/frontend/railway.toml` | Yes | Next.js dashboard + public menu |
| `cafino-worker` | `/backend` | `/backend/railway-worker.toml` | No | Celery background jobs |
| `cafino-beat` | `/backend` | `/backend/railway-beat.toml` | No | Celery schedules |
| PostgreSQL | Railway PostgreSQL | — | No | Primary SaaS database |
| Redis | Railway Redis | — | No | Celery broker |

For worker and beat, set the **Custom Config File** in Railway to the paths above. The API can use the default `/backend/railway.toml` and the frontend `/frontend/railway.toml`.

## 1. Databases

Add PostgreSQL and Redis to the Railway project. Reference their variables instead of copying credentials manually.

Backend / worker / beat variables:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
```

The API is the only service that runs migrations. `railway.toml` runs `python manage.py migrate --noinput` as a pre-deploy command; if migrations fail, the new deployment must not go live.

## 2. Backend variables

Generate a public domain for `cafino-backend`, then set:

```text
CAF_INO_ENV=saas
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<strong-random-secret>
DJANGO_TIME_ZONE=Asia/Tehran
DJANGO_SECURE_SSL_REDIRECT=1
DJANGO_HSTS_SECONDS=3600
DJANGO_DB_CONN_MAX_AGE=60
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=60
```

Railway-provided `RAILWAY_PUBLIC_DOMAIN` and `RAILWAY_PRIVATE_DOMAIN` are automatically appended to Django `ALLOWED_HOSTS`. You may still set explicit custom hosts:

```text
DJANGO_ALLOWED_HOSTS=api.example.com
```

After the frontend domain exists, set on Backend:

```text
CAF_INO_FRONTEND_ORIGIN=https://<frontend-domain>
```

Multiple origins are comma-separated. This value is added to both CORS and CSRF trusted origins. Public non-debug deployments reject non-HTTPS frontend origins.

For a custom backend domain also add it to `DJANGO_ALLOWED_HOSTS`.

## 3. Frontend variables

Generate the backend public domain first. On `cafino-frontend` set these before building:

```text
NEXT_PUBLIC_API_ROOT=https://<backend-domain>
NEXT_PUBLIC_API_URL=https://<backend-domain>/api/v1
```

These are browser-visible build-time variables. After changing either value, redeploy the frontend.

Generate the frontend public domain and copy it into Backend `CAF_INO_FRONTEND_ORIGIN`.

## 4. Worker and Beat

Both services use the `/backend` root and the same `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `DJANGO_SECRET_KEY`, `CAF_INO_ENV=saas`, and Django security variables as Backend.

They do not need public networking.

Worker command is defined in `/backend/railway-worker.toml`:

```text
celery -A config worker -l INFO --concurrency=${CELERY_WORKER_CONCURRENCY:-2}
```

Beat command is defined in `/backend/railway-beat.toml` and writes its local schedule under `/tmp`; durable scheduling state is not business data.

Run exactly one Beat replica.

## 5. First Business and Owner — no demo seed

Do not use development/demo seed data on a production Railway database.

After the first successful migration, set a temporary Railway variable on the Backend service:

```text
CAF_INO_BOOTSTRAP_OWNER_PASSWORD=<strong-temporary-password>
```

Then run a one-off command in the Backend service/container:

```bash
python manage.py bootstrap_business_owner \
  --business-name "Your Cafe" \
  --username "owner" \
  --email "owner@example.com" \
  --branch-name "Main" \
  --deployment-type SAAS
```

The command:

- validates the password using Django password validators,
- creates no demo product/order/inventory data,
- creates or safely reuses the exact Business and Branch,
- creates an `OWNER` tenant user,
- is idempotent and does **not** reset an existing matching owner's password by default,
- fails instead of taking over a username belonging to another tenant/role,
- refuses an existing business with a mismatched deployment profile.

After a successful bootstrap, remove `CAF_INO_BOOTSTRAP_OWNER_PASSWORD` from Railway variables. To deliberately rotate the same owner's password, set the temporary variable again and run the command with `--reset-password`, then remove it again.

## 6. Optional Production Operations

The central web deployment can act as the Cafino Local Operations Control Plane. Configure the same **public** Ed25519 license verification key used by Local releases:

```text
CAF_INO_LICENSE_PUBLIC_KEY_PEM=<public-key-pem>
```

Never deploy the private licensing key.

Local clients can then be built with:

```text
CAF_INO_OPS_ENDPOINT=https://<backend-domain>/api/ops/v1
```

## 7. Health checks

Backend Railway health check:

```text
/api/v1/health/
```

It is public and returns a small service status only.

Frontend health check:

```text
/login
```

Do not use authenticated pages for Railway health checks.

## 8. First production deploy order

1. Create PostgreSQL and Redis.
2. Deploy Backend and generate its public domain.
3. Set Backend production variables and database/Redis references.
4. Deploy Worker and Beat with the same private service references.
5. Set Frontend `NEXT_PUBLIC_API_ROOT` and `NEXT_PUBLIC_API_URL` to the Backend HTTPS URL.
6. Deploy Frontend and generate its public domain.
7. Add the Frontend HTTPS origin to Backend `CAF_INO_FRONTEND_ORIGIN`, then redeploy Backend.
8. Open `/api/v1/health/` and `/login`.
9. Run `bootstrap_business_owner`, then remove its temporary password variable.
10. Log in as the Owner, run Settings → Onboarding, then Settings → Go-Live.
11. Test product creation, checkout, kitchen flow, online menu, SMS queue and reports.

## 9. Production acceptance

Before public use verify:

- `DJANGO_DEBUG=0`.
- strong `DJANGO_SECRET_KEY` is configured.
- PostgreSQL is used; never SQLite for SaaS.
- Redis is private and Worker/Beat are running.
- Backend and Frontend are HTTPS.
- CORS/CSRF list only the intended frontend origins.
- migrations completed in pre-deploy.
- Backend health check is green.
- only one Beat replica exists.
- temporary bootstrap password variable has been removed.
- database backups are enabled in Railway/project policy.
- Settings → Go-Live reports the SaaS profile ready.

## 10. Local vs Web hardware boundary

The browser SaaS edition cannot directly access Windows POS-terminal SDKs, USB/serial devices or local printers. Hardware integration remains in Cafino Local/Electron. The same web UI detects the Electron bridge and uses it when present; in a normal web browser POS payments remain manual/online unless a separate local hardware bridge is deliberately installed.
