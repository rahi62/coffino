# Cafino Railway Release Checklist

Use this checklist after PR validation/merge when creating the real Web/SaaS pilot on Railway.

## 1. Services

Create six services/resources in one Railway project/environment:

| Name | Source / Root | Config as Code | Public |
|---|---|---|---|
| `cafino-backend` | repo, `/backend` | `/backend/railway.toml` | Yes |
| `cafino-frontend` | repo, `/frontend` | `/frontend/railway.toml` | Yes |
| `cafino-worker` | repo, `/backend` | `/backend/railway-worker.toml` | No |
| `cafino-beat` | repo, `/backend` | `/backend/railway-beat.toml` | No |
| `Postgres` | Railway PostgreSQL | — | No |
| `Redis` | Railway Redis | — | No |

Important: Railway's Config File path does **not** follow the service Root Directory. Set the absolute repository path shown above.

Run exactly one `cafino-beat` replica.

## 2. Backend variables

Start from `backend/.env.railway.example`.

Required blockers checked by `python manage.py railway_preflight` before migrations:

- `CAF_INO_ENV=saas` (or `dedicated`).
- `DJANGO_DEBUG=0`.
- non-placeholder `DJANGO_SECRET_KEY`.
- PostgreSQL database engine.
- Railway Redis broker, not localhost.
- SSL redirect enabled and HSTS greater than zero.
- no wildcard `*` in `DJANGO_ALLOWED_HOSTS`.
- public CORS/CSRF origins use HTTPS.
- Railway healthcheck hostname is accepted automatically when Railway variables are present.

Use Railway reference variables:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
```

Backend pre-deploy order is intentionally:

```text
python manage.py railway_preflight
python manage.py migrate --noinput
```

If either command fails, do not route traffic to the new deployment.

## 3. Frontend variables

Start from `frontend/.env.railway.example`.

```text
NEXT_PUBLIC_API_ROOT=https://<backend-public-domain>
NEXT_PUBLIC_API_URL=https://<backend-public-domain>/api/v1
```

These values are public and are compiled into the Next.js client bundle. The Frontend Dockerfile declares them as build `ARG`s so Railway service variables are available during Docker build. Redeploy Frontend after changing either URL.

## 4. Monorepo settings

For each service, verify both values in Railway Settings:

```text
Backend:  Root Directory=/backend   Config File=/backend/railway.toml
Frontend: Root Directory=/frontend  Config File=/frontend/railway.toml
Worker:   Root Directory=/backend   Config File=/backend/railway-worker.toml
Beat:     Root Directory=/backend   Config File=/backend/railway-beat.toml
```

Optional Watch Paths can prevent unrelated rebuilds:

```text
/backend/**
/frontend/**
```

Use the matching path for each service. Worker/Beat/Backend all use `/backend/**`.

## 5. First deploy order

1. Provision PostgreSQL and Redis.
2. Create/configure Backend and set DB/Redis/security variables.
3. Generate Backend public HTTPS domain.
4. Deploy Backend; preflight + migrations + `/api/v1/health/` must pass.
5. Create Worker and Beat using the same Backend environment/security/database variables.
6. Configure Frontend `NEXT_PUBLIC_API_*` with Backend public HTTPS URL.
7. Deploy Frontend and generate its public HTTPS domain.
8. Set Backend `CAF_INO_FRONTEND_ORIGIN=https://<frontend-domain>` and redeploy Backend.
9. Confirm browser login can reach Backend without CORS/CSRF errors.
10. Create the first tenant Owner with `bootstrap_business_owner` and remove the temporary password variable immediately afterward.

## 6. First tenant

Temporarily add to Backend only:

```text
CAF_INO_BOOTSTRAP_OWNER_PASSWORD=<strong-temporary-password>
```

Then execute inside the Backend service environment:

```bash
python manage.py bootstrap_business_owner \
  --business-name "Pilot Cafe" \
  --username "owner" \
  --email "owner@example.com" \
  --branch-name "Main" \
  --deployment-type SAAS
```

Remove `CAF_INO_BOOTSTRAP_OWNER_PASSWORD` immediately after success.

Do not run `seed_demo` on the production database.

## 7. Acceptance endpoints

Before business-flow testing:

```text
GET https://<backend>/api/v1/health/       -> HTTP 200
GET https://<frontend>/login               -> HTTP 200
```

Railway's deploy-time healthcheck uses host `healthcheck.railway.app`; Cafino adds it only when Railway runtime variables are detected.

## 8. SaaS acceptance flow

Run at least:

```text
Login
→ Settings / Onboarding
→ Branch
→ Catalog / Product
→ Cash register
→ Order + Checkout
→ Kitchen flow
→ Receipt payload
→ Inventory movement
→ Online menu
→ Online order
→ Notifications queue
→ Reports
→ Settings / Go-Live
```

Also verify Worker and Beat logs show healthy Celery connectivity and only one Beat scheduler is active.

## 9. Release decision

Do not call the SaaS pilot ready until all are true:

- PR/`main` CI is green on PostgreSQL, Next, Electron/static contracts and installer contract.
- Railway Backend preflight and migrations succeed.
- Backend/Frontend healthchecks are exact HTTP 200.
- first Owner can log in.
- a real checkout completes and appears in reports.
- Redis/Worker/Beat are healthy.
- Settings → Go-Live has no deployment blockers.
- database backup policy is enabled at the Railway/PostgreSQL level.

Hardware (printer/card terminal) remains a Cafino Local/Electron acceptance concern and does not run directly inside the browser SaaS deployment.
