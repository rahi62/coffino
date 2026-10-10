# Cafino SaaS Identity and OTP Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver tenant-safe SaaS registration, ParsGreen-backed OTP verification, refresh-aware JWT authentication, password recovery, and customer mobile verification without breaking existing username/password users.

**Architecture:** A platform-owned OTP domain stores hashed, purpose-bound challenges and calls ParsGreen through a replaceable provider adapter. Purpose-specific APIs consume short-lived verification grants; tenant creation stays in an atomic registration service, while dashboard users and customer identities remain separate. The frontend centralizes access/refresh handling and adds Persian registration, OTP login, recovery, and customer-verification flows.

**Tech Stack:** Django 5.1/5.2, Django REST Framework, SimpleJWT, PostgreSQL/SQLite tests, Redis-compatible DRF throttling, Celery, Next.js 16, React 19, TypeScript 5.7, Node built-in test runner.

**Spec:** `docs/superpowers/specs/2026-10-10-saas-identity-otp-foundation-design.md`

## Global Constraints

- Preserve existing users, username/password login, roles, tenant scoping, Local first-run, operational onboarding, POS payments, `PaymentGatewayConfig`, and `BusinessModule` behavior.
- Public registration always creates an active SAAS Business, active primary Branch, and active OWNER in one transaction.
- Anonymous clients never choose `business_id`, `branch_id`, role, permissions, deployment type, modules, or subscription state.
- Dashboard mobile is globally unique when present; Customer phone remains tenant-owned and is not a dashboard identity.
- Platform OTP covers registration, dashboard login, recovery, and customer verification; branch SMS remains responsible for order-ready and marketing messages.
- OTP policy defaults to six digits, five-minute expiry, sixty-second resend cooldown, and five verification attempts.
- ParsGreen credentials and raw OTP codes never enter source control, logs, browser bundles, public errors, or Celery task arguments.
- Do not auto-retry an ambiguous ParsGreen timeout.
- Do not add subscription, billing, payment, trial, entitlement, or plan-enforcement logic.
- Keep localStorage token compatibility for this milestone; HttpOnly-cookie migration is out of scope.
- All user-facing frontend copy and actionable API validation messages must be Persian and understandable.
- Commit locally after every task. Do not push or deploy.

## Review Focus

- Iranian mobile input in `09…`, `+98…`, `0098…`, Persian-digit, and Arabic-digit forms must normalize identically; landlines and malformed values must fail safely (Task 1 tests).
- Duplicate or concurrent OTP requests must respect cooldown and must not create an unbounded set of active challenges or resend after ambiguous provider failure (Task 2 tests).
- A customer verification grant from Business A must never authorize an online order, wallet debit, or loyalty redemption in Business B (Task 6 tests).
- Concurrent frontend 401 responses must share one refresh request, retry each original request at most once, and redirect only after refresh failure (Task 7 tests).
- Registration failure after Business or Branch creation must roll back Business, Branch, User, and grant consumption together (Task 3 tests).

---

## File Structure

New backend files:

- `backend/apps/accounts/phone.py`: Iranian mobile normalization and masking.
- `backend/apps/accounts/otp.py`: challenge lifecycle, hashing, verification grants, and purpose rules.
- `backend/apps/accounts/otp_providers.py`: `OtpSender`, fake sender, and ParsGreen adapter.
- `backend/apps/accounts/registration.py`: public SAAS owner registration service.
- `backend/apps/accounts/tokens.py`: JWT pair issuance, refresh serializer, and token invalidation checks.
- `backend/apps/accounts/authentication.py`: JWT authentication enforcing `tokens_invalid_before`.
- `backend/apps/accounts/recovery.py`: generic account resolution and password reset orchestration.
- `backend/apps/accounts/serializers.py`: public auth request validation.
- `backend/apps/accounts/views.py`: thin public registration/login/recovery views.
- `backend/apps/accounts/urls.py`: versioned auth routes.
- `backend/apps/accounts/throttles.py`: named public-auth throttle classes.
- `backend/apps/accounts/tests_identity.py`, `tests_otp.py`, `tests_registration.py`, `tests_auth_api.py`, `tests_recovery.py`: focused backend tests.
- `backend/apps/customers/verification.py`: customer-specific grant consumption and verification state.
- `backend/apps/customers/tests_verification.py`: customer tenant-bound verification tests.
- `frontend/src/lib/auth.ts`: browser session API.
- `frontend/src/lib/auth-session.mjs`: pure single-flight refresh/session primitives testable by Node.
- `frontend/tests/auth-session.test.mjs`: Node built-in auth lifecycle tests.
- `frontend/src/lib/registration-state.mjs`: pure registration step/validation state.
- `frontend/tests/registration-state.test.mjs`: registration flow tests.
- `frontend/src/lib/customer-verification-state.mjs`: pure recovery/customer OTP state.
- `frontend/tests/customer-verification-state.test.mjs`: recovery and customer verification flow tests.
- `frontend/src/components/otp-form.tsx`: reusable Persian OTP request/verify form.
- `frontend/src/app/register/page.tsx`, `forgot-password/page.tsx`, `reset-password/page.tsx`: public account pages.

Existing files modified only for integration:

- account/customer models, migrations, admin, settings, Celery schedule, root URLs, `/me/`, public ordering, checkout/loyalty operations, auth guard, login, POS/loyalty/online-order UI, API client, package scripts, environment examples, and operational documentation.

### Task 1: Mobile Identity Schema and Normalization

**Files:**
- Create: `backend/apps/accounts/phone.py`
- Create: `backend/apps/accounts/tests_identity.py`
- Modify: `backend/apps/accounts/models.py`
- Modify: `backend/apps/accounts/admin.py`
- Modify: `backend/apps/customers/models.py`
- Modify: `backend/apps/customers/admin.py`
- Create: `backend/apps/accounts/migrations/0004_user_mobile_and_otp_challenge.py`
- Create: `backend/apps/customers/migrations/0004_customer_phone_verification.py`

**Interfaces:**
- Produces: `normalize_iran_mobile(value: str) -> str`, `mask_mobile(value: str) -> str`.
- Produces: nullable `User.mobile`, `User.mobile_verified_at`, `User.tokens_invalid_before`.
- Produces: `OtpChallenge` with `Purpose` enum and helper state properties.
- Produces: nullable `Customer.phone_normalized` and `Customer.phone_verified_at`.

- [ ] **Step 1: Write failing normalization and model tests**

Add tests named `test_normalizes_supported_iran_mobile_formats`, `test_rejects_non_mobile_and_malformed_values`, `test_non_null_user_mobile_is_globally_unique`, and `test_legacy_users_and_customers_remain_valid_with_null_fields`. Assert Persian/Arabic digits and `+98`/`0098` variants normalize to the same `09xxxxxxxxx` value.

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_identity -v 2`

Expected: collection/import failure because `phone.py` and fields do not exist.

- [ ] **Step 3: Implement normalization, models, admin exposure, and migrations**

Use `normalize_iran_mobile(value: str) -> str` as the only normalization entry point. Store a UUID public ID, `code_hash`, purpose, expiry/cooldown timestamps, attempt limits, consumed timestamp, optional user/business FKs, delivery state, provider code, and correlation ID on `OtpChallenge`; never add a raw-code field.

- [ ] **Step 4: Verify migrations and tests**

Run: `backend/.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run`

Expected: `No changes detected`.

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_identity -v 2`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts backend/apps/customers
git commit -m "feat: add mobile identity and OTP challenge schema"
```

### Task 2: OTP Domain Service and ParsGreen Adapter

**Files:**
- Create: `backend/apps/accounts/otp.py`
- Create: `backend/apps/accounts/otp_providers.py`
- Create: `backend/apps/accounts/throttles.py`
- Create: `backend/apps/accounts/tests_otp.py`
- Modify: `backend/config/settings.py`
- Modify: `backend/apps/accounts/models.py`
- Modify: `backend/config/celery.py` or `backend/config/settings.py` for pruning schedule
- Modify: `backend/.env.example`
- Modify: `deploy/vps/backend.env.example`

**Interfaces:**
- Consumes: `normalize_iran_mobile()`, `OtpChallenge`.
- Produces: `request_otp(*, mobile: str, purpose: str, user=None, business=None, request_ip='') -> OtpRequestResult`.
- Produces: `verify_otp(*, challenge_id: UUID, code: str, expected_purpose: str, expected_business_id: int | None = None) -> str` returning a signed verification grant.
- Produces: `consume_verification_grant(token: str, *, purpose: str, business_id: int | None = None) -> VerifiedOtp`.
- Produces: `OtpSender.send(*, mobile: str, code: str, correlation_id: str) -> OtpDeliveryResult`.

- [ ] **Step 1: Write failing OTP lifecycle and provider-contract tests**

Cover success, bad code, expiry, fifth failed attempt lockout, used challenge, resend cooldown, normalized-phone/IP throttles, malformed provider response, provider `R_Success=false`, safe timeout handling, and the Review Focus concurrent/ambiguous cases. Patch network transport; assert the ParsGreen request uses `/Apiv2/Message/SendOtp`, JSON keys `Mobile`, `SmsCode`, `AddName`, HTTPS, and Basic authorization without exposing credentials.

- [ ] **Step 2: Run tests and confirm failure**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_otp -v 2`

Expected: FAIL because OTP services/providers do not exist.

- [ ] **Step 3: Implement the OTP service, fake sender, ParsGreen sender, settings, and pruning**

Hash codes with Django password hashing, sign grants with a dedicated salt, compare purpose/business on consumption, and consume within `transaction.atomic()`. Dispatch OTP synchronously so the user receives immediate delivery status; do not place raw codes in Celery. Add a scheduled cleanup task that deletes only expired/consumed challenges older than the retention window.

- [ ] **Step 4: Run focused tests and configuration checks**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_otp -v 2`

Expected: PASS with no real network calls.

Run: `backend/.venv/Scripts/python.exe backend/manage.py check`

Expected: no system-check errors with ParsGreen disabled and no secrets configured.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts backend/config backend/.env.example deploy/vps/backend.env.example
git commit -m "feat: add secure OTP service and ParsGreen adapter"
```

### Task 3: Atomic SaaS Registration API

**Files:**
- Create: `backend/apps/accounts/registration.py`
- Create: `backend/apps/accounts/serializers.py`
- Create: `backend/apps/accounts/views.py`
- Create: `backend/apps/accounts/urls.py`
- Create: `backend/apps/accounts/tests_registration.py`
- Modify: `backend/apps/accounts/bootstrap.py`
- Modify: `backend/config/urls.py`
- Modify: `backend/config/settings.py`

**Interfaces:**
- Consumes: `consume_verification_grant(... purpose=SAAS_REGISTRATION)`, shared owner-password validation.
- Produces: `register_saas_owner(*, business_name: str, business_type: str, branch_name: str, branch_phone: str, username: str, email: str, password: str, verification_grant: str) -> RegistrationResult`.
- Produces: registration OTP request/verify endpoints and `POST /api/v1/auth/register/`.

- [ ] **Step 1: Write failing service/API tests**

Cover the twelve registration requirements from the product prompt plus Persian validation responses. Explicitly patch User creation to fail after Business and Branch creation and assert all counts and grant consumption roll back. Assert unknown privileged fields (`role`, `business_id`, `branch_id`, `deployment_type`, permissions/modules) produce 400.

- [ ] **Step 2: Run registration tests and confirm failure**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_registration -v 2`

Expected: FAIL because registration service and routes do not exist.

- [ ] **Step 3: Centralize owner password validation and implement registration**

Keep administrative bootstrap idempotency unchanged. Registration performs availability checks, consumes proof, creates SAAS Business/Branch/OWNER, and optionally copies the verified owner mobile to Branch phone only when explicitly requested.

- [ ] **Step 4: Run registration, bootstrap, local-bootstrap, and tenant tests**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_registration apps.accounts.tests_bootstrap apps.core.tests_local_bootstrap apps.core.tests_security -v 2`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts backend/config/urls.py backend/config/settings.py
git commit -m "feat: add atomic SaaS owner registration API"
```

### Task 4: JWT Issuance, Refresh, Revocation, and Auth Context

**Files:**
- Create: `backend/apps/accounts/tokens.py`
- Create: `backend/apps/accounts/authentication.py`
- Create: `backend/apps/accounts/tests_auth_api.py`
- Modify: `backend/apps/accounts/views.py`
- Modify: `backend/apps/accounts/serializers.py`
- Modify: `backend/apps/accounts/urls.py`
- Modify: `backend/config/urls.py`
- Modify: `backend/config/settings.py`
- Modify: `backend/apps/core/api/operations.py`

**Interfaces:**
- Consumes: verified `STAFF_LOGIN` grant.
- Produces: `issue_token_pair(user: User) -> dict[str, str]`.
- Produces: `CafinoJWTAuthentication`, `CafinoTokenObtainPairView`, `CafinoTokenRefreshView`.
- Produces: OTP login request/verify endpoints returning the same access/refresh shape as password login.

- [ ] **Step 1: Write failing authentication tests**

Cover legacy password login, OTP login for exactly one active verified user, generic missing-account OTP response, valid refresh, invalid refresh, token rejection after `tokens_invalid_before`, throttled login, and `/me/` fields `email`, `mobile`, `mobile_verified`, `business_id`, and `branch_id` without sensitive fields.

- [ ] **Step 2: Run tests and confirm failure**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_auth_api -v 2`

Expected: FAIL against current token views and `/me/` response.

- [ ] **Step 3: Implement custom token views/authentication and OTP login**

Preserve `/api/token/` and `/api/token/refresh/` URLs. Validate both access and refresh `iat` against `tokens_invalid_before`; accept existing tokens for users whose invalidation timestamp is null.

- [ ] **Step 4: Run auth and existing permission tests**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_auth_api apps.accounts.tests apps.core.tests_onboarding_permissions -v 2`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts backend/apps/core/api/operations.py backend/config
git commit -m "feat: add OTP login and revocable JWT lifecycle"
```

### Task 5: Password Recovery Backend

**Files:**
- Create: `backend/apps/accounts/recovery.py`
- Create: `backend/apps/accounts/notifiers.py`
- Create: `backend/apps/accounts/tests_recovery.py`
- Modify: `backend/apps/accounts/serializers.py`
- Modify: `backend/apps/accounts/views.py`
- Modify: `backend/apps/accounts/urls.py`
- Modify: `backend/config/settings.py`
- Modify: `backend/.env.example`

**Interfaces:**
- Consumes: OTP service, shared strong-password validator, `tokens_invalid_before`.
- Produces: `request_password_recovery(identifier: str, request_ip: str) -> None` with generic external behavior.
- Produces: `reset_password(*, reset_grant: str, password: str, confirmation: str) -> User`.
- Produces: provider-neutral `AccountRecoveryNotifier` for legacy email fallback.

- [ ] **Step 1: Write failing recovery tests**

Cover identical existing/missing responses, ambiguous duplicate legacy email, verified-mobile OTP, mock email fallback, valid reset, weak password, invalid/expired/used proof, old password rejection, new password success, and rejection of pre-reset access/refresh tokens.

- [ ] **Step 2: Run tests and confirm failure**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_recovery -v 2`

Expected: FAIL because recovery services/routes do not exist.

- [ ] **Step 3: Implement recovery orchestration and endpoints**

Resolve username exactly, mobile canonically, and email case-insensitively only when exactly one active user matches. Keep public response content and status identical regardless of lookup outcome. On successful reset, set `tokens_invalid_before` and consume the proof in the same transaction.

- [ ] **Step 4: Run recovery and auth regression tests**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts.tests_recovery apps.accounts.tests_auth_api -v 2`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts backend/config/settings.py backend/.env.example
git commit -m "feat: add enumeration-safe password recovery"
```

### Task 6: Tenant-Bound Customer Verification and Sensitive Operations

**Files:**
- Create: `backend/apps/customers/verification.py`
- Create: `backend/apps/customers/tests_verification.py`
- Modify: `backend/apps/core/api/public.py`
- Modify: `backend/apps/core/api/operations.py`
- Modify: `backend/apps/core/urls.py`
- Modify: `backend/apps/core/serializers.py`
- Modify: `backend/apps/core/api/viewsets_tenant_catalog.py`
- Modify: `backend/apps/payments/services.py` only if the service signature needs explicit verified-customer context

**Interfaces:**
- Consumes: `CUSTOMER_VERIFY` grants bound to Business and mobile.
- Produces: public-menu customer OTP request/verify endpoints deriving Business from `OnlineMenuSettings.public_slug`.
- Produces: authenticated customer OTP request/verify endpoints deriving Business from the authenticated user's tenant.
- Produces: `require_customer_verification(*, grant: str, customer: Customer, business_id: int, purpose: str) -> None`.

- [ ] **Step 1: Write failing tenant/security tests**

Cover unverified POS capture, verified status update, public-menu tenant derivation, online-order proof requirement, grant/mobile mismatch, Business A proof against Business B, replay, loyalty redemption without/with proof, and wallet checkout/split settlement without/with proof.

- [ ] **Step 2: Run tests and confirm failure**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.customers.tests_verification -v 2`

Expected: FAIL because verification endpoints and enforcement do not exist.

- [ ] **Step 3: Implement customer verification and enforcement**

Normalize new customer writes through one service, preserve legacy duplicates, and reject ambiguous matches rather than merging silently. Online order creation consumes a business-bound proof. Financial customer-value operations require a proof bound to the exact customer phone and tenant.

- [ ] **Step 4: Run customer, public security, payment, and loyalty tests**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.customers.tests_verification apps.core.tests_public_security apps.payments apps.loyalty -v 2`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/customers backend/apps/core backend/apps/payments
git commit -m "feat: enforce tenant-bound customer mobile verification"
```

### Task 7: Refresh-Aware Frontend Auth Client

**Files:**
- Create: `frontend/src/lib/auth-session.mjs`
- Create: `frontend/src/lib/auth.ts`
- Create: `frontend/tests/auth-session.test.mjs`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/auth-guard.tsx`
- Modify: `frontend/package.json`

**Interfaces:**
- Produces: `getAccessToken()`, `getRefreshToken()`, `setSession()`, `clearSession()`, `loginWithPassword()`, `loginWithOtp()`, `refreshSession()`, and `logout()`.
- Produces: authenticated `api()` behavior that retries once after a shared refresh.

- [ ] **Step 1: Write failing Node tests for session behavior**

Use `node:test` and injected fetch/storage/navigation fakes. Cover access/refresh storage, complete logout cleanup, successful 401-refresh-retry, one refresh for concurrent 401s, no infinite retry, failed refresh cleanup, and redirect to `/login` only after refresh failure.

- [ ] **Step 2: Add the test script and confirm failure**

Run: `npm.cmd --prefix frontend test`

Expected: FAIL because auth-session primitives do not exist.

- [ ] **Step 3: Implement session primitives, auth wrapper, API retry, and AuthGuard public routes**

Public routes are `/login`, `/register`, `/forgot-password`, `/reset-password`, and `/menu/*`. Keep current token keys readable during migration and remove both old and new auth keys on logout.

- [ ] **Step 4: Run frontend tests and type/build validation**

Run: `npm.cmd --prefix frontend test`

Expected: PASS.

Run: `npm.cmd --prefix frontend run build`

Expected: successful Next.js production build.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib frontend/src/components/auth-guard.tsx frontend/tests frontend/package.json
git commit -m "feat: add refresh-aware frontend auth client"
```

### Task 8: Registration and Dual-Method Login Frontend

**Files:**
- Create: `frontend/src/components/otp-form.tsx`
- Create: `frontend/src/app/register/page.tsx`
- Create: `frontend/src/lib/registration-state.mjs`
- Create: `frontend/tests/registration-state.test.mjs`
- Modify: `frontend/src/app/login/page.tsx`
- Modify: `frontend/src/lib/auth.ts`
- Modify: `frontend/src/lib/i18n.ts`
- Add or modify: focused frontend contract tests under `frontend/tests/`

**Interfaces:**
- Consumes: registration OTP endpoints, `POST /auth/register/`, password/OTP login functions.
- Produces: reusable OTP request/verify UI and registration completion redirect to `/settings/onboarding`.

- [ ] **Step 1: Add failing validation/route contract tests**

Test pure registration state transitions, required verified mobile before account fields, password confirmation, explicit branch-phone copy flag, and login-method selection. Keep Local setup detection in the existing page and verify it through an exported pure decision helper rather than adding a React test framework.

- [ ] **Step 2: Run tests and confirm failure**

Run: `npm.cmd --prefix frontend test`

Expected: FAIL for missing registration/OTP UI contracts.

- [ ] **Step 3: Implement responsive Persian registration and login flows**

Use the existing login visual language. Do not expose role, tenant, deployment, module, or internal identifiers. Auto-login with the chosen password after successful registration and redirect to existing onboarding.

- [ ] **Step 4: Run tests and production build**

Run: `npm.cmd --prefix frontend test`

Run: `npm.cmd --prefix frontend run build`

Expected: both PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/login frontend/src/app/register frontend/src/components/otp-form.tsx frontend/src/lib frontend/tests
git commit -m "feat: add verified SaaS registration and OTP login UI"
```

### Task 9: Recovery and Customer Verification Frontend

**Files:**
- Create: `frontend/src/app/forgot-password/page.tsx`
- Create: `frontend/src/app/reset-password/page.tsx`
- Create: `frontend/src/lib/customer-verification-state.mjs`
- Create: `frontend/tests/customer-verification-state.test.mjs`
- Modify: `frontend/src/app/menu/[slug]/page.tsx`
- Modify: `frontend/src/app/pos/page.tsx`
- Modify: `frontend/src/app/customers-loyalty/page.tsx`
- Modify: `frontend/src/app/split-bill/page.tsx` if wallet settlement is exposed there
- Modify: `frontend/src/lib/api.ts`
- Add or modify: focused frontend tests under `frontend/tests/`

**Interfaces:**
- Consumes: recovery APIs and customer-verification APIs/grants.
- Produces: generic recovery success UX, reset completion redirect, online-order OTP dialog, verified/unverified customer indicator, and OTP proof collection for loyalty/wallet operations.

- [ ] **Step 1: Add failing UI contract tests**

Cover pure recovery/reset validation, online order blocked until verification, POS unverified capture allowed, and loyalty/wallet proof attached only after successful OTP. Route components consume these pure helpers; production build supplies the component-level integration check without adding a React test framework.

- [ ] **Step 2: Run tests and confirm failure**

Run: `npm.cmd --prefix frontend test`

Expected: FAIL for missing recovery/customer flows.

- [ ] **Step 3: Implement recovery and customer verification UX**

Use modal OTP confirmation where it avoids navigation loss. Keep POS checkout fast and optional, but require verification before online order creation and customer-value consumption. All errors remain Persian and provider-neutral.

- [ ] **Step 4: Run tests and responsive production build**

Run: `npm.cmd --prefix frontend test`

Run: `npm.cmd --prefix frontend run build`

Expected: both PASS with no horizontal overflow introduced on mobile routes.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app frontend/src/lib frontend/tests
git commit -m "feat: add recovery and customer mobile verification UX"
```

### Task 10: Tenant Audit, Operational Documentation, and Final Verification

**Files:**
- Modify: `backend/apps/core/tests_security.py`
- Modify: `backend/apps/core/tests_onboarding_permissions.py`
- Modify: `docs/LOGIN_AND_USER_MANAGEMENT.md`
- Create: `docs/SAAS_IDENTITY_OTP_OPERATIONS.md`
- Modify: environment/deployment examples only if verification finds missing documented variables

**Interfaces:**
- Consumes: all prior task interfaces.
- Produces: release evidence, operator setup instructions, rollback/disable procedure, and complete tenant-adjacent regression coverage.

- [ ] **Step 1: Extend focused tenant audit tests**

For a newly registered OWNER, test `/me/`, permissions, settings context, onboarding, user creation/reset, Business and Branch list/detail/mutation, own-tenant access, and other-tenant denial. Include direct cross-tenant IDs and nested branch IDs.

- [ ] **Step 2: Run the focused security suite**

Run: `backend/.venv/Scripts/python.exe backend/manage.py test apps.accounts apps.customers apps.core.tests_security apps.core.tests_onboarding_permissions apps.core.tests_public_security -v 2`

Expected: PASS.

- [ ] **Step 3: Document operations and compatibility**

Document required environment names, fake/live provider modes, health checks, safe credential rotation, disabling OTP while retaining password login, no-live-SMS test policy, Local first-run behavior, localStorage tradeoff, and the deferred billing/quota work. Do not include credential values.

- [ ] **Step 4: Run final verification**

Run: `backend/.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run`

Run: `backend/.venv/Scripts/python.exe backend/manage.py check --deploy`

Run: `backend/.venv/Scripts/python.exe -m compileall backend/apps backend/config`

Run: `backend/.venv/Scripts/python.exe backend/manage.py test -v 1`

Run: `npm.cmd --prefix frontend test`

Run: `npm.cmd --prefix frontend run build`

Run: `git grep -n -I -E 'PARSGREEN_(API_KEY|SIGNATURE)=.+|SmsCode.{0,20}(print|log)' -- ':!docs/superpowers/*'`

Expected: migrations clean; deploy check has no new blocking errors; compilation, backend tests, frontend tests/build pass; secret scan returns no committed values or OTP logging.

- [ ] **Step 5: Review Git scope and commit documentation/tests**

Run: `git status --short` and `git diff --stat origin/main...HEAD`.

Confirm `AGENT.md`, the preserved generated-file stash, credentials, databases, bytecode, and build artifacts are not staged.

```bash
git add backend/apps/core/tests_security.py backend/apps/core/tests_onboarding_permissions.py docs/LOGIN_AND_USER_MANAGEMENT.md docs/SAAS_IDENTITY_OTP_OPERATIONS.md
git commit -m "test: verify SaaS identity release boundaries"
```

Do not push or deploy. Provide the final implementation report and leave publishing to the user.
