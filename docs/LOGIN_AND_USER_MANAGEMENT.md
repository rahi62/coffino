# ورود، ثبت‌نام و مدیریت هویت Cafino

## محیط Production

- Frontend: `https://cafeno.digitalafarin.ir`
- Backend API: `https://cafenoapi.digitalafarin.ir`
- Django Admin: `https://cafenoapi.digitalafarin.ir/admin/`

GitHub منبع اصلی حقیقت است. تغییرات identity قبل از انتشار باید از CI عبور کنند و سپس در Coolify deploy شوند.

## مسیرهای ورود

Cafino دو روش ورود را پشتیبانی می‌کند:

1. نام کاربری + گذرواژه برای سازگاری با حساب‌های فعلی.
2. شماره همراه تأییدشده + OTP برای حساب‌هایی که mobile verified دارند.

Endpointهای اصلی:

- `POST /api/token/`
- `POST /api/token/refresh/`
- `POST /api/v1/auth/login/otp/request/`
- `POST /api/v1/auth/login/otp/verify/`
- `GET /api/v1/me/`

Frontend access و refresh token را موقتاً در localStorage نگه می‌دارد. API client روی 401 فقط یک بار refresh انجام می‌دهد و request را یک بار retry می‌کند. اگر refresh ناموفق باشد session پاک و کاربر به `/login` هدایت می‌شود.

مهاجرت به HttpOnly cookie یک تغییر معماری جداگانه است و بدون طراحی کامل CSRF نباید نیمه‌کاره انجام شود.

## ثبت‌نام SaaS

ثبت‌نام عمومی از `/register` انجام می‌شود.

جریان:

```text
Owner Mobile
→ OTP Verification
→ Business Details
→ OWNER Account
→ Primary Branch
→ Atomic Registration
→ Password Login
→ /settings/onboarding
```

Backend tenant را ایجاد می‌کند. Anonymous client اجازه تعیین این موارد را ندارد:

- business_id
- branch_id
- role
- permission_overrides
- deployment_type
- enabled_modules

ثبت‌نام موفق در یک transaction، یک Business از نوع SAAS، یک Branch و یک OWNER ایجاد می‌کند.

## بازیابی گذرواژه

مسیرهای Frontend:

- `/forgot-password`
- `/reset-password`

Endpointها:

- `POST /api/v1/auth/password/forgot/`
- `POST /api/v1/auth/password/otp/verify/`
- `POST /api/v1/auth/password/reset/`

Forgot-password برای حساب موجود و ناموجود پاسخ عمومی یکسان می‌دهد تا account enumeration ایجاد نشود. در این milestone بازیابی واقعی برای حسابی انجام می‌شود که شماره همراه تأییدشده داشته باشد. حساب legacy بدون mobile verified پاسخ عمومی دریافت می‌کند ولی تا اضافه‌شدن notifier جایگزین، کد دریافت نمی‌کند.

پس از reset موفق، `tokens_invalid_before` به‌روز می‌شود و access/refresh tokenهای قدیمی دیگر معتبر نیستند.

## Local first-run

Local first-run از SaaS registration جداست. Endpoint `/api/v1/local/bootstrap/` فقط وقتی فعال است که deployment واقعاً Local و دیتابیس SQLite تازه باشد.

این مسیر نباید در SaaS Production برای ساخت tenant استفاده شود.

## نقش‌ها و Tenant

نقش‌های فعلی:

- OWNER
- MANAGER
- CASHIER
- WAITER
- KITCHEN
- INVENTORY
- ACCOUNTANT

کاربر non-superuser همیشه باید به Business معتبر متصل باشد. نقش‌های عملیاتی باید Branch داشته باشند. OWNER و MANAGER می‌توانند business-level باشند.

Tenant isolation در API با tenancy helpers و `BaseVS` enforce می‌شود؛ پنهان‌کردن منو در Frontend مرز امنیتی محسوب نمی‌شود.

## ساخت اعضای تیم

مالک/مدیر مجاز از بخش تنظیمات تیم می‌تواند کاربران عملیاتی بسازد. برای هر نفر حساب جداگانه ایجاد شود و نقش/شعبه حداقل لازم اختصاص داده شود.

از حساب مشترک، credential نمونه و superuser برای کار روزمره Production استفاده نشود.
