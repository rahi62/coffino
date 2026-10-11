# SaaS Identity & OTP Operations

## Scope

این سند عملیات Milestone 1 هویت SaaS را پوشش می‌دهد:

- SaaS owner registration
- password login
- OTP login
- JWT refresh/revocation
- password recovery
- ParsGreen OTP adapter
- tenant-safe identity boundaries

Subscription، Billing و SaaS payment در این milestone وجود ندارند.

## Production URLs

```text
Frontend  https://cafeno.digitalafarin.ir
Backend   https://cafenoapi.digitalafarin.ir
```

Frontend باید هنگام build این متغیرهای public را دریافت کند:

```env
NEXT_PUBLIC_API_ROOT=https://cafenoapi.digitalafarin.ir
NEXT_PUBLIC_API_URL=https://cafenoapi.digitalafarin.ir/api/v1
```

چون `NEXT_PUBLIC_*` در Next.js build-time است، تغییر آن نیازمند rebuild/redeploy Frontend است.

## Required Backend Environment

نمونه نام متغیرها، بدون secret value:

```env
CAF_INO_ENV=saas
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=cafenoapi.digitalafarin.ir
CAF_INO_FRONTEND_ORIGIN=https://cafeno.digitalafarin.ir
CORS_ALLOWED_ORIGINS=https://cafeno.digitalafarin.ir
CSRF_TRUSTED_ORIGINS=https://cafeno.digitalafarin.ir

DATABASE_URL=...
REDIS_URL=...
CELERY_BROKER_URL=...
DJANGO_CACHE_URL=...

PARSGREEN_OTP_ENABLED=0
PARSGREEN_API_BASE_URL=https://sms.parsgreen.ir
PARSGREEN_API_KEY=...
PARSGREEN_SIGNATURE=...
PARSGREEN_OTP_ADD_NAME=1
PARSGREEN_TIMEOUT_SECONDS=10

CAF_INO_OTP_TTL_SECONDS=300
CAF_INO_OTP_GRANT_TTL_SECONDS=300
CAF_INO_OTP_RESEND_SECONDS=60
CAF_INO_OTP_MAX_ATTEMPTS=5
CAF_INO_OTP_SEND_LIMIT_PER_HOUR=5
CAF_INO_OTP_VERIFY_LIMIT_PER_HOUR=20
CAF_INO_OTP_RETENTION_DAYS=7
```

Secretها فقط در environment/secret store محیط اجرا قرار می‌گیرند و نباید در Git، frontend bundle یا log نوشته شوند.

## Redis / Rate Limits

در Production مقدار `DJANGO_CACHE_URL` باید به Redis قابل دسترس Backend اشاره کند. OTP cooldown و abuse controls نباید در چند replica به LocMem وابسته باشند.

Celery می‌تواند Redis DB دیگری استفاده کند. جداسازی logical DB برای cache و broker توصیه می‌شود.

## Safe Rollout

ترتیب انتشار:

1. PostgreSQL backup معتبر قبل از migration.
2. Backend deploy با migrations.
3. Backend health/API checks.
4. ParsGreen را ابتدا disabled نگه دارید.
5. Frontend build با API domain production.
6. تست password login کاربر legacy.
7. تست registration با provider کنترل‌شده.
8. فقط پس از اعتبارسنجی provider credentials، `PARSGREEN_OTP_ENABLED=1`.
9. Worker و Beat را بعد از backend code/migrations سازگار restart کنید.

هیچ migration مربوط به این milestone نباید Business/User فعلی را حذف یا email را globally unique کند.

## Health / Smoke Checks

بدون نمایش secret:

```text
GET  /api/v1/health/
POST /api/token/
POST /api/token/refresh/
GET  /api/v1/me/
```

برای OTP، تست production فقط با شماره تست مجاز انجام شود. OTP code و credential provider در log ثبت نشوند.

## Disable OTP Safely

در incident مربوط به provider:

```env
PARSGREEN_OTP_ENABLED=0
```

سپس Backend restart/redeploy شود.

Password login موجود باقی می‌ماند. Disable کردن OTP نباید کاربران legacy را از ورود با username/password محروم کند.

ثبت‌نام عمومی که verification موبایل لازم دارد تا زمان بازگشت provider عملاً قابل تکمیل نخواهد بود؛ UI باید خطای provider-neutral نشان دهد.

## Password Reset Security

Recovery request پاسخ generic می‌دهد. Proof از OTP grant کوتاه‌عمر و single-use ساخته می‌شود.

Reset موفق:

- password را با policy مشترک validate می‌کند؛
- proof را consume می‌کند؛
- `tokens_invalid_before` را به‌روزرسانی می‌کند؛
- access/refresh tokenهای قبل از reset را باطل می‌کند.

## Token Storage

Frontend فعلاً برای backward-compatible delivery، access/refresh را در localStorage ذخیره می‌کند.

ریسک اصلی: XSS می‌تواند به token دسترسی پیدا کند. بنابراین:

- هیچ HTML غیرقابل اعتماد با `dangerouslySetInnerHTML` وارد نشود؛
- CSP و dependency hygiene در hardening بعدی بررسی شود؛
- مهاجرت به HttpOnly cookie فقط همراه CSRF design کامل انجام شود.

## Tenant Boundary

Registration هیچ tenant identifier از anonymous client قبول نمی‌کند.

هر tenant جدید server-side ساخته می‌شود:

```text
Business(SAAS)
├── OWNER
└── Primary Branch
```

پس از ثبت‌نام، همان OWNER فقط باید Business/Branch خودش را از tenant-scoped API ببیند.

## Database Changes

Identity milestone migrationها nullable/backward-compatible هستند:

- User.mobile
- User.mobile_verified_at
- User.tokens_invalid_before
- OtpChallenge
- Customer.phone_normalized
- Customer.phone_verified_at

قبل از Production deploy migration plan را از release بررسی کنید. هیچ uniqueness روی legacy customer phone/email اضافه نشده است.

## Rollback Notes

Rollback کد بعد از اجرای migrationهای additive معمولاً ممکن است بدون حذف column/table انجام شود؛ migration reverse در Production بدون بررسی داده انجام نشود.

اگر frontend مشکل داشت، frontend release را rollback کنید و backend additive schema را نگه دارید.

اگر OTP provider مشکل داشت، provider را disable کنید و password login را حفظ کنید.

## Deferred Work

عمداً به milestone بعد منتقل شده:

- HttpOnly cookie auth
- email recovery notifier برای legacy account
- subscription / plan / entitlement
- SaaS billing / payment
- customer-value OTP enforcement در POS/online ordering


## Trusted reverse proxies

DRF throttling and OTP abuse controls use the same client-IP resolution policy.

`CAF_INO_NUM_PROXIES` must equal the number of trusted reverse proxies between the browser and Django. A value of `0` ignores forwarded IP headers and uses `REMOTE_ADDR`. Do not increase this value without verifying the actual Coolify/proxy chain, because trusting untrusted forwarded headers weakens IP-based throttling.


## Django Admin — Global OTP Provider

ParsGreen OTP can now be managed globally from Django Admin through **Platform OTP Provider Config**.

This configuration is platform-level; it is intentionally separate from the branch-level `SmsProviderConfig` used for restaurant/cafe operational notifications.

Precedence is deterministic:

1. If no `PlatformOtpProviderConfig` row exists, existing environment variables remain the fallback.
2. Once the global database row exists, it becomes authoritative.
3. A disabled row disables platform OTP even if the old env toggle is enabled.
4. An enabled row with missing/decryption-failed credentials fails closed; it never falls back silently to env secrets.

Security behavior:

- API Key and Signature are encrypted at rest using the existing Cafino secret-encryption helper.
- Existing secret values are never rendered back into the Admin form.
- Leaving a secret field blank preserves the stored value.
- Only Django superusers can view or modify the global OTP provider configuration.
- The Admin action **ارسال OTP آزمایشی به شماره تست** validates actual provider delivery without exposing the generated OTP code in the panel or logs.

Important: encryption currently derives from `DJANGO_SECRET_KEY`. Rotating that key requires re-entering encrypted provider credentials afterward.
