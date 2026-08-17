# Cafino Local — Production Release Runbook

This runbook covers the Windows Local edition only. The production build is intentionally stricter than a development/unsigned build.

## 1. One-time offline license keys

Generate an Ed25519 key pair on a trusted machine:

```powershell
node scripts/generate-license-keypair.js
```

Default output:

- `release-secrets/license-private-key.pem` — keep offline and never commit/upload to the app.
- `release-secrets/license-public-key.pem` — package this public key with Cafino Local.

The application verifies licenses with the public key only.

## 2. Windows signing certificate

Production release requires electron-builder signing credentials:

```powershell
$env:CSC_LINK="<pfx path, URL, or supported certificate reference>"
$env:CSC_KEY_PASSWORD="<certificate password>"
```

Do not commit signing credentials. The production script refuses to continue without them unless `-AllowUnsigned` is explicitly used for a non-production/pilot scenario.

## 3. Update endpoint

Cafino Local uses `electron-updater` with the NSIS target and a generic HTTPS update endpoint.

Set:

```powershell
$env:CAF_INO_UPDATE_URL="https://updates.example.com/cafino/local"
```

The update directory must serve the files produced by electron-builder for the stable channel, including the installer, `latest.yml` and blockmap files. Generic-provider uploads are an operational deployment step; the app only consumes them.

## 4. Production build

```powershell
$env:CAF_INO_LICENSE_PUBLIC_KEY_PATH="C:\secure\cafino\license-public-key.pem"
$env:CAF_INO_UPDATE_URL="https://updates.example.com/cafino/local"
$env:CSC_LINK="C:\secure\cafino\codesign.pfx"
$env:CSC_KEY_PASSWORD="..."

.\scripts\build-release.ps1 -Production
```

Production build gates:

- static release contract
- no migration drift
- migrations apply
- Django deployment checks
- full backend tests
- PyInstaller backend build
- Next.js production build
- Electron release tests
- NSIS installer build
- Windows signing required
- SHA-256 release manifest generated

Artifacts are under `electron/release/`.

## 5. GitHub Actions signed build

Workflow: `Cafino Local Production Release`.

Required repository secrets:

- `CAF_INO_UPDATE_URL`
- `CAF_INO_LICENSE_PUBLIC_KEY_PEM`
- `CSC_LINK`
- `CSC_KEY_PASSWORD`

Run the workflow manually and provide a SemVer version such as `1.2.0`. The workflow produces a signed installer bundle as a GitHub Actions artifact. Deployment to the generic update host remains a separate controlled step.

## 6. Customer offline activation

On a production Local build with license enforcement enabled, startup is blocked until a valid license exists.

On the customer device:

1. Copy the Request Code shown by Cafino.
2. On the trusted licensing machine, set the private key path:

```powershell
$env:CAF_INO_LICENSE_PRIVATE_KEY_PATH="C:\secure\cafino\license-private-key.pem"
```

3. Issue the license:

```powershell
node scripts/issue-license.js --request "<REQUEST_CODE>" --customer "Cafe Name" --license-id "CAF-000123" --expires "2027-12-31T23:59:59Z" --out "CAF-000123.license"
```

4. Transfer only the resulting `.license` file to the customer device.
5. Import it from the native startup dialog or Settings → Release & License.

The license is bound to the hashed machine identity and is verified cryptographically. Editing the payload invalidates the signature.

## 7. Backup policy

Default Local policy:

- automatic backup interval: 24 hours
- retained backups: 14
- maximum age: 60 days

Override at build time if required:

```powershell
$env:CAF_INO_BACKUP_INTERVAL_HOURS="12"
$env:CAF_INO_BACKUP_RETENTION_COUNT="30"
$env:CAF_INO_BACKUP_MAX_AGE_DAYS="90"
```

Backups use the existing verified SQLite flow and are pruned only after a successful backup.

## 8. Safe update flow

1. Cafino checks the configured HTTPS update endpoint.
2. Operator downloads the update from Settings → Release & License.
3. Before installation, Cafino creates and verifies a `pre-update` database backup.
4. An update recovery journal records current version, target version, backup path and backup hash.
5. The NSIS updater installs and restarts Cafino.
6. New runtime must pass backend health verification.
7. If health verification fails, the recovery journal is marked `recovery_required` and the pre-update backup is preserved.

## 9. Rollback boundary

Database rollback and binary rollback are deliberately separate.

If a new binary is unhealthy:

1. Do **not** silently restore an old database while continuing to run the new binary.
2. Reinstall the previous signed Cafino installer.
3. Restore the pre-update database backup from Backup/Restore.
4. Re-run Go-Live / Local Runtime Preflight.

Keep at least one previous signed installer available for production rollback.

## 10. Release acceptance

A production release should not be delivered unless:

- CI is green.
- Signed installer is built.
- release manifest hashes are stored with the release.
- update endpoint serves matching metadata/artifacts.
- license activation is tested on a clean Windows machine.
- backup → restore drill passes on the target device.
- previous signed installer is retained for rollback.
