# Cafino Settings Dashboard Patch v1.0.0

این Patch بر اساس همان `coffino.zip` آپلودشده ساخته شده است؛ برای Overlay روی نسخه قدیمی دیگری طراحی نشده است.

## خروجی محصول

بعد از اعمال Patch، Owner/Manager از مسیر `/settings` به تنظیمات روزمره کسب‌وکار دسترسی دارد و برای این موارد به Django Admin وابسته نیست:

- Business Profile + Business Modules
- Branch Profile + Cash Register Definition
- Hall / Table Definition
- Fiscal / Tax / Service Charge
- Catalog / Product / Recipe / Inventory entrypoints
- Online Menu / QR / Delivery Zone / Payment Gateway
- SMS / Web Push provider settings
- Team: Create User / Role / Branch / Password Reset / Permission Matrix

Django Admin باقی می‌ماند اما برای Platform Support و recovery است، نه workflow عادی مشتری.

## کنترل دسترسی

- Permission جدید: `settings.manage`
- OWNER / MANAGER به‌صورت role wildcard دسترسی دارند.
- Operational roleها به Settings Hub دسترسی ندارند مگر override صریح.
- تغییر تعریف Hall / Table / Cash Register به `settings.manage` منتقل شده است.
- عملیات روزانه Table و Cash Shift همچنان Permission عملیاتی خودش را دارد.
- Manager نمی‌تواند OWNER بسازد، نقش OWNER بدهد، Permission او را تغییر دهد یا رمز OWNER را Reset کند.

## Business Modules

`BusinessModule.enabled` دیگر نمایشی نیست. Explicitly disabled module، Permissionهای عملیاتی مرتبط را در Backend Gate می‌کند. Missing module row برای backward compatibility فعال در نظر گرفته می‌شود.

## Audit

Dashboard config create/update رویدادهای `CONFIG_CREATED` و `CONFIG_UPDATED` می‌سازد. Secret-like fieldها قبل از ذخیره snapshot به‌صورت recursive ماسک می‌شوند.

Migration جدید:

`backend/apps/audit/migrations/0004_auditlog_business.py`

`AuditLog.business` امکان Audit صحیح تنظیمات سطح Business را می‌دهد.

## Patch Safety

`patch-manifest.json` برای هر فایل modified، SHA256 فایل پایه‌ای که در ZIP آپلودی بود را نگه می‌دارد.

- Base hash صحیح → فایل Patch می‌شود.
- New hash از قبل وجود دارد → Skip.
- Hash متفاوت → Conflict و توقف؛ هیچ overwrite خاموشی انجام نمی‌شود.

## اجرا

```bat
apply-settings-patch.bat "D:\path\to\coffino"
```

یا:

```powershell
powershell -ExecutionPolicy Bypass -File .\apply-settings-patch.ps1 -ProjectRoot "D:\path\to\coffino"
```

Validation بیشتر:

```powershell
.\apply-settings-patch.ps1 -ProjectRoot "D:\path\to\coffino" -Validate
```

اگر `backend/.venv/Scripts/python.exe` موجود باشد، Installer خودکار `migrate` و `manage.py check` را اجرا می‌کند. با `-Validate` تست Settings و در صورت وجود `frontend/node_modules`، `npm run build` نیز اجرا می‌شود.

## Backup / Rollback

قبل از کپی فایل‌های موجود، Backup در این مسیر ساخته می‌شود:

`patch-backups/settings-dashboard-YYYYMMDD-HHMMSS/`

Rollback فایل‌ها:

```powershell
.\rollback-settings-patch.ps1 -ProjectRoot "D:\path\to\coffino" -BackupPath "D:\path\to\coffino\patch-backups\settings-dashboard-..."
```

Rollback دیتابیس عمداً خودکار نیست. برای rollback schema از برنامه migration/backup دیتابیس خود استفاده کن.

## Validation انجام‌شده هنگام ساخت Patch

- Cafino static release gate: PASS
- Python AST: 303 files / 0 errors
- committed migrations detected: 79
- TS/TSX syntax transpile: 64 files / 0 errors
- Electron main/preload syntax: PASS

Django runtime test suite و Next production build در محیط Artifact اجرا نشدند چون dependencyهای پروژه در آن محیط نصب نیستند. CI اضافه‌شده و `scripts/build-release.ps1` مرجع Runtime Validation هستند.
