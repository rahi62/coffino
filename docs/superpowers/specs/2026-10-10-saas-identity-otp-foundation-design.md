# Cafino SaaS Identity and OTP Foundation

Date: 2026-10-10

Status: Approved conversational design, pending written-spec review

> Release scope note (2026-10-11): Customer phone verification and customer-value enforcement described later in this design are deferred to a separate milestone. The current SaaS Identity Foundation release covers owner registration, dashboard authentication/OTP, JWT refresh/revocation, password recovery, tenant boundaries, and related frontend flows only.

## 1. Purpose

This milestone establishes public SaaS registration, backward-compatible authentication, password recovery, and mobile verification for Cafino. It also introduces a platform-level ParsGreen OTP integration without coupling tenant operations to a specific SMS vendor.

The intended product outcome is:

- a new business owner can register without administrator assistance;
- the owner's mobile number is verified before any tenant data is created;
- existing users can continue signing in with username and password;
- verified dashboard users may also sign in with OTP;
- customers can be captured quickly at POS and verified only when an operation requires proof of phone ownership;
- identity, tenant ownership, operational SMS, and customer records remain separate security domains.

This milestone does not introduce subscriptions, billing, payment, trials, entitlements, or plan enforcement.

## 2. Verified Current Baseline

The current backend uses Django, Django REST Framework, SimpleJWT, PostgreSQL, Redis, Celery Worker, and Celery Beat. The frontend uses Next.js and TypeScript.

Current behavior verified before this design:

- `User` extends `AbstractUser` and contains `business`, `branch`, `role`, and `permission_overrides`.
- `username` is the authoritative unique login identifier.
- `/api/token/` and `/api/token/refresh/` are available.
- the frontend stores only the access token and logs out immediately on a 401.
- `/api/v1/me/` validates the current session.
- `bootstrap_business_owner()` already provides an atomic administrative bootstrap service.
- local first-run bootstrap is restricted to LOCAL deployments with SQLite.
- `BaseVS` and tenancy helpers provide secure-by-default tenant scoping.
- `Customer` is branch-scoped and currently stores a non-unique free-form phone value.
- operational SMS configuration is branch-scoped through `SmsProviderConfig`.
- the POS already supports customer lookup by name or phone.

The local branch was fast-forwarded to `origin/main` at `2d09cb95f01c551466f7572cfcdb955cfbe95e65` before writing this design.

## 3. Core Decisions

### 3.1 Hybrid SMS responsibility

Platform identity messages are the responsibility of Cafino:

- owner registration OTP;
- dashboard user OTP login;
- password recovery OTP;
- customer phone verification OTP.

Tenant operational and commercial messages remain the business's responsibility:

- order-ready notifications;
- marketing and campaigns;
- other branch-generated messages.

This split removes setup friction from SaaS onboarding while preventing a tenant's missing credit or broken SMS configuration from disabling authentication.

### 3.2 Separate dashboard identity from customer identity

`User.mobile` identifies a dashboard account. It is globally unique when present because OTP login must resolve to exactly one user.

`Customer.phone` remains tenant-owned customer data. The same phone may be present as a customer in multiple businesses and may also belong to a dashboard user. A customer record never grants dashboard access.

### 3.3 Preserve password login

Username/password login remains supported. OTP is an additional sign-in method, not a replacement. Public SaaS registration is the exception: the initial owner must verify a mobile number before registration can complete.

### 3.4 Provider isolation

Application services depend on an internal `OtpSender` contract. ParsGreen is implemented as an adapter. Views, serializers, registration services, and customer services must not call ParsGreen directly.

## 4. ParsGreen Provider Contract

The official Swagger contract exposes:

- method: `POST`;
- URL: `https://sms.parsgreen.ir/Apiv2/Message/SendOtp`;
- content type: `application/json`;
- authorization header: Basic authentication using `api_key:signature`;
- request fields: `Mobile`, `SmsCode`, and `AddName`;
- response fields: `R_Success`, `R_Code`, `R_Error`, and `R_Message`.

The adapter will:

- generate no OTP itself; it receives the application-generated code;
- normalize Iranian mobile numbers before sending;
- use HTTPS only;
- apply explicit connect/read timeouts;
- validate HTTP status and response shape;
- treat `R_Success != true` as provider failure;
- expose normalized internal errors without returning provider internals to public clients;
- never log the API key, signature, OTP code, or full mobile number;
- not retry an ambiguous send automatically, because a timeout may occur after ParsGreen accepted the message;
- support a fake sender in development and tests.

Before enabling live delivery, the Basic authorization encoding and a successful response must be verified in a non-production ParsGreen account. No real SMS is sent during implementation or automated tests.

## 5. Data Model

### 5.1 User additions

Add to `accounts.User`:

- `mobile`: nullable, blank, normalized Iranian mobile, globally unique when non-null;
- `mobile_verified_at`: nullable datetime;
- `tokens_invalid_before`: nullable datetime used to invalidate JWTs issued before a password reset or security event.

Existing users migrate with all three fields null. Their username/password login remains unchanged.

### 5.2 OTP challenge

Add an `OtpChallenge` model owned by the platform identity domain:

- random public identifier;
- normalized mobile;
- purpose enum;
- hashed OTP code;
- creation and expiration timestamps;
- next allowed send timestamp;
- failed-attempt count and maximum attempts;
- consumed timestamp;
- optional user relation for login or recovery;
- optional business relation for tenant-scoped customer verification;
- non-sensitive delivery state and provider result code;
- correlation identifier safe for internal diagnostics.

Purposes:

- `SAAS_REGISTRATION`;
- `STAFF_LOGIN`;
- `PASSWORD_RECOVERY`;
- `CUSTOMER_VERIFY`.

Raw OTP values are never persisted. Old challenges are periodically pruned by Celery Beat.

### 5.3 Customer additions

Add to `customers.Customer`:

- `phone_normalized`: nullable/blank canonical value;
- `phone_verified_at`: nullable datetime.

No database uniqueness constraint is added to existing customer phone data in this milestone. Existing duplicates must not break deployment. New lookup and write services normalize values and handle ambiguity conservatively.

### 5.4 Verification grants

Successful OTP verification returns a short-lived, signed, purpose-specific verification grant. A grant contains only the minimum server-verified claims:

- normalized mobile;
- purpose;
- challenge identifier;
- optional business identifier for customer verification;
- issued-at and expiry timestamps.

The consuming endpoint verifies purpose and tenant binding and atomically marks the challenge consumed. A registration grant cannot be used for login or customer verification.

## 6. Backend Components

### 6.1 Registration service

Create a dedicated `register_saas_owner()` service in the accounts domain. It may reuse the centralized owner password validator but must not call the local bootstrap endpoint or `BusinessVS.create`.

Accepted fields:

- business name and type;
- primary branch name and optional branch phone;
- username;
- email;
- password and confirmation;
- verified registration grant.

It never accepts `business_id`, `branch_id`, `role`, permissions, deployment type, enabled modules, or subscription state.

Within one database transaction it:

1. validates and consumes the registration grant;
2. verifies username and case-insensitive email availability using the current compatibility policy;
3. verifies global mobile availability;
4. creates an active SAAS Business;
5. creates its active primary Branch;
6. creates an active OWNER attached to the new Business with no branch restriction;
7. saves the verified mobile and timestamp;
8. commits only if every step succeeds.

The owner mobile can be copied to `Branch.phone` only when the user explicitly selects that option. Owner mobile and branch contact phone remain distinct concepts.

### 6.2 OTP service

The OTP application service owns:

- normalization;
- secure code generation;
- hashing and constant-time verification;
- resend cooldown;
- expiration;
- attempt counting and lockout;
- challenge consumption;
- purpose and tenant binding;
- provider dispatch through `OtpSender`;
- safe audit metadata.

Default policy, configurable through settings:

- six numeric digits;
- five-minute lifetime;
- sixty-second resend cooldown;
- five verification attempts;
- phone- and IP-aware throttling;
- one active challenge per phone and purpose where practical.

### 6.3 Authentication and JWT lifecycle

Password login keeps `/api/token/` and gains appropriate throttling.

OTP login is permitted only when exactly one active user has the verified mobile. Successful verification issues the same access/refresh JWT pair as password login.

JWT handling will include `tokens_invalid_before`. Custom authentication and refresh validation reject tokens whose `iat` precedes that timestamp. Password reset updates the timestamp, invalidating earlier access and refresh tokens without requiring a destructive migration or immediate logout of all existing users.

### 6.4 Password recovery

Recovery request accepts username, email, or mobile and always returns the same public response. Resolution rules avoid ambiguous legacy email matches.

- users with a verified mobile receive a platform OTP;
- legacy users without a verified mobile can use the provider-neutral email notifier when configured;
- no account existence is revealed through response content;
- reset uses the shared strong password policy;
- successful reset consumes the recovery proof and invalidates older JWTs;
- used or expired proof cannot reset again.

### 6.5 Customer verification

POS staff may create or update an unverified customer without OTP. This keeps counter service fast.

OTP proof is required before:

- an online customer places an order;
- wallet value is used;
- loyalty points are redeemed;
- other future customer-owned sensitive actions.

A customer verification grant is bound to both mobile and Business. A grant from one business cannot verify or mutate customer data in another tenant.

## 7. Public API Shape

Use purpose-specific endpoints backed by the shared OTP service. This avoids trusting a caller-supplied purpose for privileged transitions.

Registration:

- `POST /api/v1/auth/register/otp/request/`
- `POST /api/v1/auth/register/otp/verify/`
- `POST /api/v1/auth/register/`

OTP login:

- `POST /api/v1/auth/login/otp/request/`
- `POST /api/v1/auth/login/otp/verify/`

Password recovery:

- `POST /api/v1/auth/password/forgot/`
- `POST /api/v1/auth/password/otp/verify/`
- `POST /api/v1/auth/password/reset/`

Customer verification will have separate authenticated POS and public online-order entry points. The public entry point derives its tenant from the trusted public-menu configuration/slug, not a caller-supplied business ID.

Public request endpoints return generic messages where account enumeration is possible. Registration may report that a mobile is already used only after the caller proves possession of that mobile.

`GET /api/v1/me/` will safely include:

- id;
- username;
- email;
- masked or normalized mobile as appropriate for the authenticated owner;
- mobile verification state;
- role;
- business ID;
- branch ID.

## 8. Frontend Design

### 8.1 Central auth client

Create a central auth module that owns:

- access and refresh token storage;
- password login;
- OTP login;
- refresh with a single shared in-flight promise;
- one retry of the original request after successful refresh;
- logout and complete auth-state cleanup;
- redirect to `/login` only when refresh fails.

LocalStorage remains temporarily for backward-compatible incremental delivery. This security tradeoff is documented. Moving to HttpOnly cookies is a separate migration requiring a complete CSRF design.

### 8.2 Pages

Create:

- `/register` as a mobile-verification-first multi-step flow;
- `/forgot-password`;
- `/reset-password`.

Update `/login` with two methods:

- username/password;
- verified mobile/OTP.

Local first-run setup remains visible only when the backend explicitly reports that it is available.

Public routes include login, registration, recovery pages, and `/menu/*`. AuthGuard uses the central refresh-aware auth client.

### 8.3 Registration UX

The registration sequence is:

1. owner mobile entry;
2. OTP verification;
3. business details;
4. owner username, email, and password;
5. primary branch details and optional explicit copy of owner mobile to branch phone;
6. atomic registration;
7. automatic login;
8. redirect to the existing settings onboarding flow.

Internal terms such as tenant ID, deployment type, role code, and BusinessModule are not exposed.

### 8.4 Customer UX

The POS continues to allow fast customer search and capture. It shows a concise verified/unverified state but does not force OTP during ordinary staff-entered checkout.

Online ordering and sensitive loyalty/wallet actions use a small OTP dialog. Error text remains Persian, understandable, and does not expose provider internals.

## 9. Security and Abuse Controls

- DRF throttles protect registration, login, recovery, OTP request, and OTP verify endpoints.
- Application-level cooldown and attempt limits remain authoritative even if cache throttling is unavailable.
- Rate-limit keys use IP plus a keyed hash of normalized mobile; raw phone numbers are not used in logs or cache keys.
- Anonymous input never selects business, branch, role, permissions, or modules.
- Cross-tenant object lookup always uses verified tenant context.
- Provider credentials exist only in backend environment variables.
- Browser bundles, API errors, audit logs, and Celery task arguments do not contain provider credentials or raw OTP codes.
- ParsGreen failures produce a generic retry-later message and do not reveal account existence.
- Ambiguous network outcomes are not automatically resent.
- OTP verification uses constant-time comparison through Django password hashing/checking primitives.
- Real SMS delivery is never enabled implicitly by DEBUG or test settings.

## 10. Migration and Rollout

1. Add nullable fields and OTP tables with backward-compatible migrations.
2. Deploy backend with ParsGreen delivery disabled unless required environment variables are present and explicitly enabled.
3. Keep existing password login and tokens valid.
4. Add frontend routes and refresh-aware auth.
5. Validate fake-provider flows in CI and local development.
6. Validate the ParsGreen contract in a controlled non-production account without exposing credentials.
7. Enable platform OTP in production only after health checks and rate-limit configuration pass.

No email uniqueness constraint and no customer-phone uniqueness constraint are introduced in this milestone.

## 11. Configuration

Expected environment variables, with final names confirmed during implementation:

- `PARSGREEN_OTP_ENABLED`
- `PARSGREEN_API_BASE_URL` with a safe default to the official HTTPS host
- `PARSGREEN_API_KEY`
- `PARSGREEN_SIGNATURE`
- `PARSGREEN_OTP_ADD_NAME`
- `PARSGREEN_CONNECT_TIMEOUT_SECONDS`
- `PARSGREEN_READ_TIMEOUT_SECONDS`
- `CAF_INO_OTP_TTL_SECONDS`
- `CAF_INO_OTP_RESEND_SECONDS`
- `CAF_INO_OTP_MAX_ATTEMPTS`
- `CAF_INO_FRONTEND_ORIGIN`

Secrets are documented by name only and are never committed.

## 12. Testing Strategy

Backend tests cover:

- successful atomic registration;
- SAAS deployment type and OWNER assignment;
- duplicate username, verified mobile, and case-insensitive email handling;
- weak password and confirmation mismatch;
- rejection of role, business ID, and other privileged fields;
- rollback after failures at each creation stage;
- local bootstrap compatibility;
- password login compatibility;
- refresh success, invalid refresh, and post-reset token invalidation;
- generic recovery responses;
- valid, invalid, expired, over-attempted, resent, and consumed OTP challenges;
- fake ParsGreen success, provider-declared error, malformed response, and timeout;
- no retry after ambiguous provider timeout;
- customer verification tenant binding;
- same-tenant access and cross-tenant denial for newly registered owners;
- `/me/`, permissions, settings context, onboarding, user management, businesses, and branches.

Frontend tests use the existing toolchain where possible and do not add a large framework solely for this milestone. They cover:

- public-route handling;
- password and OTP login navigation;
- registration validation and step transitions;
- logout cleanup;
- one-time 401 refresh and retry;
- shared refresh for concurrent requests;
- failed refresh redirect;
- OTP dialog states and Persian user-facing errors.

Final verification includes the affected Django test suite, migration checks, Python compilation, frontend build/type checking, and repository secret scanning.

## 13. Commit and Delivery Policy

Implementation is divided into focused commits for schema/domain, registration API, OTP adapter, auth lifecycle, recovery, customer verification, frontend flows, and tests/documentation.

Commits are created locally. Nothing is pushed or deployed during implementation. The user will review and push after the milestone is complete.

## 14. Known Risks and Deferred Work

- LocalStorage JWTs remain exposed to successful XSS; HttpOnly cookie migration is deferred as an explicit auth architecture project.
- Legacy users without verified mobile cannot use OTP login until they add and verify a number.
- Legacy duplicate emails require conservative recovery behavior and a later data audit.
- Existing customer phone duplicates are not automatically merged.
- ParsGreen production behavior and Basic authorization formatting require a controlled non-production contract check before live enablement.
- SMS cost allocation, quotas, subscription entitlements, and tenant billing are intentionally deferred.
- Tenant-owned provider routing for high-volume customer OTP may be added later without changing the application-level OTP contract.

## 15. Completion Criteria

The milestone is complete when:

- an anonymous owner verifies a mobile and atomically creates a Business, Branch, and OWNER;
- privileged tenant fields cannot be supplied by the anonymous client;
- existing username/password login still works;
- verified dashboard users can log in by OTP;
- access-token expiration refreshes once without a refresh storm;
- password reset invalidates earlier JWTs;
- customer verification is tenant-bound and required for online/sensitive customer actions;
- ordinary POS customer capture remains fast and can remain unverified;
- Local first-run behavior remains LOCAL-only;
- affected backend tests and frontend build/tests pass;
- no subscription, billing, or payment logic is introduced;
- all changes are committed locally and nothing is pushed or deployed.
