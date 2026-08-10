# Cafino Settings Dashboard

Cafino business users should not depend on Django Admin for normal configuration. Django Admin remains a platform/support tool; tenant configuration lives under `/settings` in the Next.js dashboard.

## Routes

```text
/settings                 Settings Hub
/settings/business        Business profile + module registry
/settings/branches        Branch profile + cash-register definitions
/settings/dining          Hall and table definitions
/settings/sales           Fiscal/tax/service-charge + sales equipment links
/settings/catalog         Product/recipe/inventory configuration entrypoints
/settings/online          Public menu + QR + delivery zones + payment gateway
/settings/notifications   SMS + Web Push provider settings
/settings/team            User creation + role/branch + password reset + Permission Matrix
```

## Operations vs settings

Definitions are separated from daily work:

- defining a cash register is Settings; opening/closing a cash shift stays in `/cashier`;
- defining a table is Settings; opening/closing a table session stays in `/tables`;
- configuring online ordering is Settings; accepting live orders stays in `/online-ordering`;
- configuring notification providers is Settings; queue/retry remains in `/notifications`.

## Access model

`settings.manage` is a dedicated permission. OWNER and MANAGER inherit it through their role wildcard. Operational roles do not.

Configuration mutation of Hall, Table and CashRegister now requires `settings.manage`; operational actions still use their operational permission such as `tables.use` or `cashier.use`.

User creation and password reset are available from the dashboard to users with `permissions.manage`. Operational users must be assigned to a Branch. Only OWNER/platform superuser can create or manage the OWNER role.

## Module registry

`BusinessModule.enabled` is now functional rather than decorative. Explicitly disabling a module gates mapped backend permissions on subsequent requests. Missing module rows preserve legacy behavior and are treated as enabled until explicitly configured.

Settings/business permissions remain available so an owner can re-enable a module.

## Audit

Generic dashboard configuration create/update flows emit:

- `CONFIG_CREATED`
- `CONFIG_UPDATED`

Team actions emit dedicated audit events.

`AuditLog` now has a nullable Business relation so business-level configuration changes are tenant-scoped even when no Branch applies. Secret-like keys are recursively masked before audit snapshots are stored.

Apply migration:

```bash
python manage.py migrate
```

## Django Admin

Django Admin is intentionally not removed. Recommended production policy:

- only platform/support staff receive `is_staff`;
- tenant owners/managers use the Cafino dashboard;
- keep `/admin` behind stronger operational controls where practical (VPN, SSO, allow-list, or equivalent infrastructure policy).

