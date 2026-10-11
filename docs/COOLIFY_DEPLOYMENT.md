# Cafino on Coolify — Production Release Guide

## Production topology

- Frontend: `https://cafeno.digitalafarin.ir`
- Backend: `https://cafenoapi.digitalafarin.ir`
- PostgreSQL: managed resource in the Cafino Coolify project
- Redis: managed resource in the Cafino Coolify project
- Worker: Celery worker service
- Beat: Celery beat service

GitHub `rahi62/coffino` is the source of truth.

## Current release rule

Feature work is completed and CI is made green on a feature branch first. Production is not used as an iterative test environment.

Release order:

```text
feature branch
→ full CI
→ review
→ merge to main
→ deploy Backend (startup runs committed migrations before Gunicorn)
→ Backend smoke test
→ deploy Frontend
→ Worker/Beat restart if backend code changed
→ Production auth/onboarding smoke test
```

## Backend variables

Use `deploy/coolify/backend.env.example` as the variable-name reference.

Secrets must be stored in Coolify and never committed:

- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `DJANGO_CACHE_URL`
- `PARSGREEN_API_KEY`
- `PARSGREEN_SIGNATURE`

The API hostname must be included in:

```env
DJANGO_ALLOWED_HOSTS=cafenoapi.digitalafarin.ir
```

The browser origin must be allowed explicitly:

```env
CAF_INO_FRONTEND_ORIGIN=https://cafeno.digitalafarin.ir
CORS_ALLOWED_ORIGINS=https://cafeno.digitalafarin.ir
CSRF_TRUSTED_ORIGINS=https://cafeno.digitalafarin.ir
```

Before release, verify the actual reverse-proxy chain. `CAF_INO_NUM_PROXIES` must match the exact number of trusted proxies in front of Django; do not guess this value if another proxy/CDN is added.

## Frontend variables

Use `deploy/coolify/frontend.env.example`.

These are build-time public variables:

```env
NEXT_PUBLIC_API_ROOT=https://cafenoapi.digitalafarin.ir
NEXT_PUBLIC_API_URL=https://cafenoapi.digitalafarin.ir/api/v1
```

Changing them requires a Frontend rebuild.

## Identity migration release

The SaaS Identity milestone contains additive account/OTP migrations. Before Production migration:

1. confirm a current PostgreSQL backup exists;
2. inspect pending migrations;
3. deploy Backend code compatible with those migrations;
4. on the current single-backend Coolify topology, `start-web.sh` runs `migrate --noinput` before Gunicorn; confirm this command actually executed and completed in deployment logs (do not separately execute concurrent migrations);
5. verify Backend health and legacy password login;
6. only then publish the new Frontend auth/registration UI.

Do not enable live ParsGreen delivery merely because the code has been deployed.

Start with:

```env
PARSGREEN_OTP_ENABLED=0
```

Enable it only after credentials and provider behavior are validated.

## Production smoke tests

After release, verify in this order:

1. Backend health endpoint responds successfully.
2. Existing username/password account still logs in.
3. `GET /api/v1/me/` works with the issued access token.
4. Access-token refresh works.
5. Login page renders without a protected Sidebar/API request.
6. Registration page stays on `/register` when anonymous.
7. Forgot-password page stays public.
8. A controlled OTP registration succeeds only after provider enablement.
9. Newly registered OWNER reaches `/settings/onboarding`.
10. Newly registered OWNER cannot read another Business/Branch.
11. Worker and Beat are healthy after backend release.

## Rollback

Frontend can be rolled back independently when no database rollback is required.

The Identity migrations are additive. Do not reverse Production migrations simply to roll back the UI. If an OTP provider incident occurs, disable OTP delivery while keeping password login available.

See also:

- `docs/SAAS_IDENTITY_OTP_OPERATIONS.md`
- `docs/LOGIN_AND_USER_MANAGEMENT.md`


## Backend startup migration policy

The Backend Dockerfile starts `/app/start-web.sh`. On the single web instance, it runs committed Django migrations before Gunicorn accepts requests. Migration failure stops web startup rather than serving incompatible API code.

Set `CAF_INO_RUN_MIGRATIONS=0` only when a dedicated migration job reliably runs before the web application. Multiple simultaneously-starting web replicas require a coordinated migration job or locking; do not use concurrent startup migrations as a general scaling strategy.

Coolify may override the image CMD through custom start commands. Verify the service has no conflicting command override before relying on this policy.


## Troubleshooting: Backend Degraded while API returns HTTP 200

Coolify's dashboard-managed HTTP healthcheck executes **inside the final application container** and requires `curl` or `wget` in that container. The Python slim base image does not guarantee either binary. The backend Dockerfile explicitly installs `curl` for this reason.

If the public `/api/v1/health/` responds with HTTP 200 but Coolify reports `running:unhealthy`:

1. Verify the actual deployed image was rebuilt from a commit containing the `curl` installation.
2. The healthcheck should target `GET http://127.0.0.1:8000/api/v1/health/` (or the verified internal `PORT`).
3. Ensure the host used by Django is present in `DJANGO_ALLOWED_HOSTS`.
4. On the container, `command -v curl` and `curl -fsS http://127.0.0.1:8000/api/v1/health/` should succeed.
5. If the process starts but remains unhealthy, inspect Docker's healthcheck output; public API reachability alone does not prove the in-container probe works.

Do not disable the healthcheck merely to hide a failing probe. Once the new image is deployed, Coolify must recreate the container to pick up the installed binary.
