# Phase: Railway SaaS + Local Installer + POS Terminal Hardening

This phase prepares Cafino for a Railway Web/SaaS pilot and a Local Windows pilot while keeping card-terminal hardware behind the Electron boundary.

## Railway

- API, Frontend, Celery Worker and Celery Beat have explicit Railway config files.
- API migrations run as a pre-deploy command.
- Django accepts Railway public/private service domains and rejects the default development secret for public SaaS/Dedicated environments.
- Frontend origins are promoted into CORS + CSRF trusted origins and require HTTPS outside DEBUG.
- Redis can be provided through `REDIS_URL`/`CELERY_BROKER_URL`.
- Gunicorn binds Railway's runtime `PORT`.
- A production-only tenant bootstrap creates the first Business/Branch/OWNER without demo data.

## Local installer

- `scripts/test-local-installer.ps1` wraps Local release build/install smoke and POS adapter contract checks.
- It refuses occupied Backend/Frontend ports and can require Authenticode for signed acceptance.

## Card terminal

Cafino Local now has a vendor-neutral terminal bridge layer:

- `MANUAL` — existing manual terminal workflow.
- `HTTP_BRIDGE` — local/private HTTP companion service.
- `TCP_JSON` — local/private newline-delimited JSON companion service.
- `EXEC_BRIDGE` — local vendor helper EXE/DLL wrapper.
- `VENDOR_SDK` — reserved for the exact PSP SDK after provider/model details are supplied.

Direct Local POS checkout requests the terminal before Django checkout, blocks declined/failed payments, and persists the approved RRN/reference number on the Payment. Transport success alone is never bank approval.

The checkout idempotency key is reused as the terminal request reference so the vendor bridge can make retries idempotent. Automatic multi-POS-tender checkout is deliberately blocked until a full multi-terminal reconciliation flow exists.

A localhost mock bridge supports end-to-end testing before real hardware arrives.

## Remaining vendor-specific input

For a real terminal integration we still need the PSP/provider, terminal make/model, connection type, SDK/protocol/sample, amount unit (Rial/Toman), response fields and reversal/status-query behavior. No production merchant/card secrets belong in the repository.
