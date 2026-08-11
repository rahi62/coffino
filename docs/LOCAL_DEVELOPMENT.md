# توسعهٔ محلی کافینو

در توسعهٔ روزمره فقط PostgreSQL و Redis با Docker اجرا می‌شوند. Django، Next.js و پردازشگرهای Celery مستقیماً روی ویندوز اجرا می‌شوند؛ بنابراین تغییر کد بدون ساخت مجدد تصویر Docker اعمال می‌شود.

## راه‌اندازی نخست

~~~
powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1
~~~

## اجرای روزمره

~~~
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
~~~

این فرمان در نخستین اجرا .env.dev را از .env.dev.example می‌سازد، PostgreSQL را روی پورت 5433 و Redis را روی پورت 6380 بالا می‌آورد، مهاجرت‌ها را اجرا می‌کند و پنجره‌های جدا برای بک‌اند، فرانت، پردازشگر وظایف و زمان‌بند باز می‌کند.

- فرانت: http://localhost:3000
- API و ادمین: http://127.0.0.1:8000
- PostgreSQL: 127.0.0.1:5433
- Redis: 127.0.0.1:6380

برای اجرای برنامهٔ دسکتاپ:

~~~
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 -Electron
~~~

برای اجرای سریع‌تر بدون Celery:

~~~
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 -NoWorkers
~~~

برای خاموش کردن زیرساخت توسعه:

~~~
powershell -ExecutionPolicy Bypass -File scripts/dev-down.ps1
~~~

Compose اصلی (docker-compose.yml) مخصوص اجرای کامل و نزدیک به انتشار است. از آن برای توسعهٔ روزانه استفاده نکنید.

اگر اجرای کامل Docker هم‌اکنون روی پورت‌های 3000 و 8000 فعال است، ابتدا سرویس‌های فرانت و بک‌اند آن را متوقف کنید؛ اسکریپت توسعه برای جلوگیری از تداخل پورت، در این وضعیت شروع نمی‌شود.
