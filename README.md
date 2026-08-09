# Cafino — Final Build

Cafino is a modular hospitality management platform built with:

- `frontend/` — Next.js + TypeScript
- `backend/` — Django + Django REST Framework
- `electron/` — Local Windows desktop runtime

The final build includes POS, orders, dining/tables, KDS, inventory/recipes, Lot/FEFO, production batches, purchasing, suppliers, cash shifts, expenses, management reporting, reservations, loyalty/wallet, gift cards, QR/online ordering, delivery/couriers, SMS/Push notifications, payment gateway flow, audit/permissions and local printing/backup.

## Clean checkout requirement

Use a clean directory for this release. Do not overlay it onto an older CoffeeSan/Coffino tree. The release gate intentionally rejects a stale `frontend/app` beside `frontend/src/app`.

## Quick local setup

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

## Build Windows installer

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-release.ps1
```

## Docker / PostgreSQL

```bash
docker compose up --build
```

## Static release check

```bash
python scripts/release-check.py
```

Committed migrations are verified with `makemigrations --check --dry-run`; setup/release never generates schema migrations.

Full deployment, architecture, security and external-integration notes are in:

`docs/FINAL_RELEASE.md`

External hardware/provider credentials are intentionally adapters: bank POS, physical pagers, SMS credentials and live payment-gateway merchant credentials must come from the selected vendor. Cafino never fakes a successful hardware/PSP operation.
