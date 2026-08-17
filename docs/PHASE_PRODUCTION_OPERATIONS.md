# Cafino Production Operations

This phase adds an optional privacy-first Operations Control Plane for Cafino Local deployments. It is deliberately separate from core POS operation: a Local installation remains usable when the control plane is unavailable.

## Safety boundary

Production Operations is **not** a remote administration shell.

The device protocol supports only:

1. signed-license device registration,
2. minimal heartbeat/health metadata,
3. fingerprint-only operational events,
4. allowlisted diagnostic snapshots,
5. release policy for staged updates and rollback guidance.

The server response contract always keeps `core_operations_allowed=true` and `remote_commands_allowed=false`. A release kill switch can pause or block updates, mark a current version unsafe and recommend rollback; it cannot remotely disable sales, cashier or other Local operations.

## Privacy contract

The Local client never intentionally sends:

- orders,
- customers,
- phone numbers,
- invoices,
- receipt content,
- raw database rows,
- raw exception messages,
- raw stack traces,
- arbitrary files.

Crash/error reporting uses SHA-256 fingerprints plus constrained component/code identifiers. Diagnostic payloads are rejected server-side if they contain fields outside the explicit allowlist.

Telemetry events are opt-in and are disabled by default. Device heartbeat and release-policy synchronization are operational metadata, not business telemetry.

## Device authentication

Initial registration requires the same Ed25519-signed Cafino Local license already used by the desktop license gate.

Registration flow:

```text
signed offline license
        ↓
POST /api/ops/v1/register/
        ↓
server verifies Ed25519 signature + machine hash + expiry
        ↓
short opaque device token returned once
        ↓
only SHA-256(token) stored by server
        ↓
raw token stored only in Local userData/ops-device.json
```

A `401` causes the Local client to discard the local device token and re-register on the next synchronization using the installed signed license.

The optional signed license fields `business_id` and `branch_id` allow an installation to be attached to the intended Control Plane tenant at first registration. Platform staff can also assign an unassigned device later.

Example license issue:

```powershell
node scripts/issue-license.js `
  --request "<REQUEST_CODE>" `
  --customer "Cafe Name" `
  --license-id "CAF-00123" `
  --business-id 12 `
  --branch-id 37 `
  --out "CAF-00123.license"
```

## Device endpoints

Public device protocol, protected by signed initial registration and then bearer device token:

```text
POST /api/ops/v1/register/
POST /api/ops/v1/heartbeat/
GET  /api/ops/v1/policy/
POST /api/ops/v1/events/
POST /api/ops/v1/diagnostics/
```

Device throttling uses a hash of the bearer token after registration so multiple installations behind the same NAT do not unnecessarily share one IP quota. Registration falls back to IP throttling.

## Management endpoints

Authenticated Cafino management API:

```text
GET  /api/v1/operations/summary/
GET  /api/v1/operations/devices/
POST /api/v1/operations/devices/<id>/diagnostics/request/
GET  /api/v1/operations/devices/<id>/diagnostics/
GET  /api/v1/operations/policies/
PATCH /api/v1/operations/policies/<stable|beta>/
```

Tenant Owner/Manager users with `operations.view` see only devices assigned to their Business. `operations.manage` allows requesting a safe diagnostic snapshot for those devices.

Release Policy mutation is intentionally restricted to Django platform superusers because rollout is a platform-wide release concern, not a tenant preference.

## Safe diagnostics allowlist

The current snapshot may contain only:

- application version,
- release channel,
- OS platform and architecture,
- backend health boolean,
- process uptime,
- database file size,
- free disk bytes,
- backup count and latest backup age,
- updater status,
- selected Printer/Pager/POS adapter identifiers.

Any unknown key causes the server to reject the complete diagnostic payload.

Diagnostic requests expire and completed/expired/cancelled snapshots are automatically pruned according to retention policy.

## Release rollout and kill switch

`ReleasePolicy` exists per `stable` / `beta` channel and includes:

- target version,
- minimum version,
- rollback version,
- rollout percentage,
- paused state,
- blocked versions,
- optional advisory message,
- optional required-after time.

Percentage rollout is deterministic:

```text
SHA256(installation_id | target_version) → bucket 0..99
```

A device therefore remains in the same rollout cohort for a specific target version across restarts and repeated heartbeat requests.

A blocked current version or a version below minimum can force update eligibility even when the ordinary rollout percentage would not include that device. Pausing a channel still stops update rollout; it never stops Local business operation.

## Retention

Default Control Plane retention:

```text
CAF_INO_OPS_EVENT_RETENTION_DAYS=90
CAF_INO_OPS_DIAGNOSTIC_RETENTION_DAYS=30
```

A daily Celery Beat task prunes old events and completed/expired/cancelled diagnostic snapshots.

## Control Plane server configuration

The Control Plane must have the Cafino license **public** key so it can independently verify Local license documents during first registration.

Example:

```bash
CAF_INO_LICENSE_PUBLIC_KEY_PATH=/run/secrets/cafino-license-public.pem
CAF_INO_OPS_EVENT_RETENTION_DAYS=90
CAF_INO_OPS_DIAGNOSTIC_RETENTION_DAYS=30
```

The private signing key remains offline and must never be deployed with either the Control Plane or Local application.

## Local build configuration

Operations integration is optional. No Ops endpoint means no dependency on the Control Plane.

```powershell
$env:CAF_INO_OPS_ENDPOINT="https://app.example.com/api/ops/v1"
$env:CAF_INO_TELEMETRY_ENABLED="0"     # default: off
$env:CAF_INO_OPS_HEARTBEAT_MINUTES="60"
.\scripts\build-release.ps1 -Production -Channel stable
```

Rules:

- endpoint must be HTTPS,
- heartbeat interval cannot be less than 15 minutes,
- telemetry events are explicitly opt-in,
- packaged smoke test validates the Operations configuration,
- `CAF_INO_OPS_ENDPOINT` is optional in the GitHub production release workflow.

## Operations dashboard

Dashboard route:

```text
/operations
```

It exposes:

- device online/offline state,
- current version/channel/health,
- recent release-health event counts,
- safe diagnostic request,
- stable/beta policy editor for platform administrators.

Local Settings → Release & License also shows the device-side Control Plane connection state, current policy, last heartbeat and whether the current version is blocked.

## Offline behavior

Control Plane failure must not block:

- opening Cafino Local,
- POS/order creation,
- payments,
- kitchen flow,
- inventory operation,
- printing,
- backups.

If Operations is unreachable the client records the connection as offline and retries later. The update policy is unavailable, so no remote command is inferred or executed.
