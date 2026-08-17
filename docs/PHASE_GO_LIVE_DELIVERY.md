# Cafino — Go-Live Delivery Phase

This phase turns setup readiness into a delivery gate for real customer installations.

## Go-Live Guard

`GET /api/v1/settings/go-live/` evaluates the selected business against its deployment model.

Checks include:
- Django DEBUG state
- non-default secret key
- deployment runtime profile (`CAF_INO_ENV`)
- expected database engine
- public host/CORS/HTTPS requirements for SaaS and Dedicated
- committed/applied migration state
- active Business and Branch
- active Owner account
- explicit enabled/disabled state for the full Cafino module catalog
- module-aware Setup Readiness
- configured Online Menu, SMS, Payment Gateway and Printer health

Warnings do not silently become blockers. The response distinguishes `ok`, `warning`, and `error`, and exposes a final `ready` decision.

## Deployment Profiles

`GET /api/v1/settings/deployment-profiles/` documents the supported delivery shapes:

### Local
- Electron + Next.js + local Django
- SQLite
- daily core operation remains independent from Cafino cloud
- local verified backup/restore
- hardware adapters through Electron

### Cloud SaaS
- PostgreSQL
- explicit public domain and HTTPS
- shared multi-tenant application infrastructure
- online ordering/payment and remote access

### Dedicated Managed
- independent PostgreSQL/server
- customer domain/branding
- managed backup and operational monitoring

The API returns a safe environment-variable template without exposing runtime secrets.

## Verified Local Backup / Restore

The local backend now validates a backup before it is accepted as recoverable.

Verification includes:
- file exists and is non-empty
- SQLite `PRAGMA integrity_check`
- SQLite `PRAGMA foreign_key_check`
- required Cafino schema tables
- migration history presence
- SHA-256 checksum
- size and verification timestamp

Restore flow:
1. verify selected source backup
2. create and verify an emergency backup of the current local database
3. stop the local backend process
4. restore the selected database
5. verify the restored target again
6. restart the backend

A corrupt or non-Cafino SQLite file is rejected before operational data is replaced.

## Local Runtime Preflight

Electron exposes a preflight report covering:
- writable Cafino data directory
- backend runtime presence
- packaged frontend runtime presence
- local database presence
- approximate free disk space
- selected device adapters

The Go-Live UI consumes this only when running inside Electron. Web/SaaS sessions correctly report that local hardware/runtime checks are unavailable.

## Device Adapter Registry

Hardware integration is no longer represented only by hard-coded POS/Pager placeholder responses.

The Electron registry currently defines:
- `PRINTER.SYSTEM` — ready through Electron/OS printers
- `PAGER.NONE` — explicitly unconfigured
- `PAGER.GENERIC_SERIAL` — planned extension point
- `POS.MANUAL` — explicit manual terminal workflow
- `POS.VENDOR_SDK` — planned SDK/API extension point

Selected adapters are controlled by:
- `CAFINO_PRINTER_ADAPTER`
- `CAFINO_PAGER_ADAPTER`
- `CAFINO_POS_ADAPTER`

Manual or planned adapters never pretend that a direct hardware transaction succeeded.

## Validation

The phase adds tests for:
- Local backup integrity/schema/checksum
- corrupt/non-Cafino backup rejection
- verified backup + restore copy behavior
- Go-Live access boundaries
- explicit module state as a delivery requirement
- Local delivery-ready path
- Device Adapter Registry contract

CI additionally checks the new adapter module syntax and contract alongside the existing PostgreSQL, Django, Next.js and Electron gates.
