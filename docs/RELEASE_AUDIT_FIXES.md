# Cafino Release Hardening — Audit Closure

This release hardening pass is based on the pre-release audit that identified three P1 blockers: frontend build/tree ambiguity, missing committed migrations, and incomplete tenant/permission isolation.

## P1-1 — Frontend tree/build hygiene

The hardened source contains **one App Router only**:

```text
frontend/src/app/
```

`frontend/app/` is intentionally absent.

Additional guards:

- `@/*` continues to resolve to `frontend/src/*`.
- `scripts/release-check.py` resolves every local `@/…` import and fails on missing files.
- the gate fails if both `frontend/app` and `frontend/src/app` exist.
- the gate fails if stale `CoffeeSan` identity exists.
- the gate fails if `next/font` is used.
- Cafino uses local/system fonts for Local-first operation.
- CI performs a real `npm run build`, not just TypeScript syntax scanning.

**Important:** extract this repository into a clean directory. Do not overlay it onto an older Coffino/CoffeeSan project tree, because stale `frontend/app` files can change Next.js routing/build behavior.

## P1-2 — Versioned migrations

All concrete Cafino model apps now ship committed baseline migrations.

The baseline is deliberately staged:

1. `0001_initial.py` — tables and scalar fields
2. `0002_relations.py` — relations after all target tables exist
3. `0003_constraints.py` — unique/check constraints after relation fields exist

This avoids cyclic app dependencies while keeping schema state versioned.

Setup and release scripts no longer generate migrations. They run:

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

CI fails if model state drifts from committed migrations.

## P1-3 — Tenant isolation and authorization

Tenant identity is explicit:

```text
User
 ├── business
 └── branch
```

Rules:

- only Django `is_superuser` is platform-global;
- every non-superuser must belong to a Business;
- operational roles must belong to a Branch;
- OWNER/MANAGER may be Business-level and branchless;
- branchless business users only receive cross-branch access through explicit permissions;
- unknown ModelViewSets fail closed (`qs.none()`) for tenant users until a scope mapping is declared.
- tenant-aware generic ViewSets also declare explicit read permissions for sensitive resources;
- generic hard-delete is denied by default; domain cancellation/deactivation flows are preferred;
- creating a new Business is restricted to Django platform superusers.

Central tenant helpers live in:

```text
backend/apps/core/tenancy.py
```

They provide business/branch assertions and queryset scoping.

### Purchase boundary

Purchasing now validates and locks:

```text
Purchase Branch
    == Supplier Branch
    == Inventory Item Branch
```

before mutation.

The purchase API requires `purchasing.manage`.

### Financial/inventory ledgers

Direct generic mutations are blocked for service-owned records such as:

- Payment
- Refund
- StockMovement
- PurchaseItem
- SupplierPayment
- CashMovement

Financial and inventory changes must use domain services/actions.

## P2 — API maintainability

The former monolithic `core/views.py` is now a compatibility export only.

Actual API code is split under:

```text
backend/apps/core/api/
├── shared.py
├── viewsets.py                 # compatibility exports
├── viewsets_tenant_catalog.py
├── viewsets_orders.py
├── viewsets_inventory.py
├── viewsets_finance.py
├── viewsets_management.py
├── operations.py
└── public.py
```

Duplicate top-level definitions are rejected by the release gate.

Public APIs now distinguish expected business validation from unexpected internal failures. Unexpected errors are logged server-side and return stable generic public error messages instead of leaking raw exception text.

## Security/regression tests

`backend/apps/core/tests_security.py` adds coverage for:

- operational user without branch rejection;
- business-level manager tenant boundaries;
- branch-only reads;
- purchase supplier/item branch mismatch;
- cross-business purchase denial;
- direct ledger mutation denial;
- report cross-branch authorization;
- cross-business stock transfer rejection;
- concurrent checkout/order-number allocation on PostgreSQL.

The PostgreSQL concurrency test is skipped on SQLite and runs in CI against PostgreSQL 17.

## CI is the release authority

`.github/workflows/ci.yml` performs:

### Backend
- install dependencies;
- Django `check`;
- migration drift check;
- apply committed migrations to PostgreSQL;
- full Django test suite on PostgreSQL.

### Frontend
- install dependencies;
- real Next.js production build.

### Electron
- install dependencies;
- syntax validation of main/preload.

### Static release gate
- Python syntax;
- migration dependency/reference lint;
- one-App-Router validation;
- local alias resolution;
- no `next/font`;
- tenant anti-pattern scan;
- Electron syntax.

## Current artifact-build environment

The environment used to assemble this ZIP has Node/Python interpreters but does not have the project Django/Next dependency sets available, and its package gateway cannot resolve all npm packages. Therefore the full Django runtime suite and Next production build cannot truthfully be marked as executed here.

They are intentionally enforced in CI and in `scripts/build-release.ps1` before installer creation.
