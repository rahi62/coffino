# Cafino — Final Release

Cafino is a modular hospitality management platform for cafés, restaurants, fast food, bakeries, pastry shops, juice/ice-cream shops, catering, hotel restaurants and chains.

## Repository

```text
cafino/
├── frontend/     Next.js + TypeScript
├── backend/      Django + DRF
├── electron/     Cafino Local desktop shell
├── scripts/      setup / dev / release checks
├── docs/
└── docker-compose.yml
```

## Final functional scope

### Sales & operations
- Order-centric POS
- Dine-in, takeaway, pickup and delivery
- Pay-before-preparation or deferred dine-in payment
- Mixed payments
- Item-level split bill
- Cash, POS, wallet, credit and gift-card tender
- Manager PIN override
- Rule-based discounts
- Void and refund workflows
- Idempotent checkout
- Order-item transfer and table-session transfer
- Kitchen Display System and station routing
- Receipt / kitchen printing through installed OS printers
- PrintJob history

### Cash & finance
- Cash registers and shifts
- CashMovement ledger
- Daily financial close and cash variance
- Expenses and fixed overheads
- Supplier debt and supplier payments
- Purchases
- Tax and service-charge snapshots
- Delivery fee
- Management COGS / gross profit / net profit
- Break-even
- KPI dashboard
- Tax collected excluded from management revenue
- Refunds reflected in recognized revenue/tax

### Inventory & production
- Inventory ledger
- Recipes
- Historical cost snapshot on OrderItem
- Lot / expiry tracking
- FEFO consumption
- Expired/blocked lots excluded from normal consumption
- Waste
- Physical inventory count
- Lot-level physical count
- Inter-branch transfer
- Production formulas
- Production batches
- Finished-goods inventory
- Production expiry/batch number
- Bakery/pastry workflow support

### Customers
- Customer history
- Loyalty points
- Loyalty tiers
- Loyalty campaigns
- Wallet
- Gift cards
- Reservations
- Online public menu
- Table QR ordering
- Pickup / takeaway / delivery ordering
- Online order status
- SMS queue
- In-app notifications
- PWA web push

### Delivery
- Delivery zones
- Minimum order / delivery fee / free-delivery threshold
- Courier profiles
- Courier assignment
- Pickup and delivery lifecycle

### Online payment
- Payment Intent
- Redirect
- Callback / webhook
- Verify before releasing order to Kitchen/Inventory
- MOCK provider for development
- ZarinPal adapter
- Generic HTTP gateway adapter
- Configurable PSP refund endpoint
- Cafino records online refunds only after the external gateway confirms the refund

### Security & control
- JWT authentication
- Role baseline + per-user permission overrides
- Branch/business scoping
- Audit log
- Manager PIN stored as a password hash
- Short-lived manager override tokens
- Encrypted SMS/payment/Push secrets
- Public API throttling
- No direct writable Order financial totals
- Payment/Refund financial flows go through services

## Local Windows

First-time developer setup:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1
```

Development:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

Create the Windows installer:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-release.ps1
```

Because this source bundle does not ship a generated npm lockfile, setup/release uses `npm install`. After the first dependency freeze, commit the generated `package-lock.json` files and you can switch CI builds to `npm ci`.

The release script:
1. runs migrations,
2. executes Django deployment checks and tests,
3. builds the local Django backend with PyInstaller,
4. builds Next.js in standalone mode,
5. copies both runtimes into Electron resources,
6. builds the NSIS installer.

The packaged Local edition stores its database and persistent encryption secret inside Electron's user-data directory. Core POS operations do not depend on Cafino cloud.

## Docker / PostgreSQL

```bash
cp .env.docker.example .env.docker
# Replace every placeholder in .env.docker with production values first.
docker compose --env-file .env.docker up --build -d
```

Docker starts PostgreSQL, Redis, Django, the Celery worker, Celery Beat and Next.js. The worker processes queued notifications and Beat schedules that processing every minute. Never use the example secrets in production.

## Demo data

After:

```bash
python manage.py seed_demo
```

Development-only credentials include:

- Admin: `admin / admin1234`
- Manager PIN: `4321`
- Cashier: `cashier / cashier1234`
- Discount code: `VIP10`

Do not use these values in production.

## External integrations

The core product is complete, but the following require credentials or hardware supplied by the actual customer/vendor:

- bank POS/card-reader SDK or vendor protocol,
- hardware pager protocol,
- SMS provider endpoint/API key,
- payment-gateway merchant credentials,
- production public domains/TLS.

Cafino does not return fake success for unavailable bank-POS or pager hardware.

For online PSP refunds, Cafino requires a configured/confirmed provider refund operation before writing the internal Refund ledger.

## Database migrations

Database migrations are committed and versioned in the repository.

Setup, CI and release must **not generate schema migrations**. They verify model drift and then apply the committed migration graph:

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

Any schema change must be accompanied by a reviewed migration committed with the source.

## Scope note

The requested final repository structure is `frontend / backend / electron`; native iOS/Android apps are therefore not added to this release. The customer-facing experience is an installable PWA with Web Push.


## Release hardening audit

The P1/P2 release-hardening changes are documented in:

`docs/RELEASE_AUDIT_FIXES.md`

For a reliable validation, use a **clean extraction** of this repository. Do not merge/overlay it onto an older CoffeeSan/Coffino frontend tree.
