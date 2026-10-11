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
→ deploy Backend
→ migrate
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
4. run migrations exactly once;
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
