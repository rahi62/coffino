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

Do not commit signing credentials. Production release refuses to continue without them unless `-AllowUnsigned` is explicitly used for a non-production/pilot build.

## 3. Stable and Beta update channels

Cafino Local uses `electron-updater` with the NSIS target and a generic HTTPS endpoint. Production builds have one immutable channel: `stable` or `beta`.

Recommended endpoint layout:

```text
https://updates.example.com/cafino/local/stable/
https://updates.example.com/cafino/local/beta/
```

The GitHub release workflow accepts a base URL:

```text
CAF_INO_UPDATE_BASE_URL=https://updates.example.com/cafino/local
```

It packages the final application update URL as `<base>/<channel>`.

The generated channel feed contains:

- `latest.yml`
- `Cafino-Setup-<version>.exe`
- installer `.blockmap`
- `release-manifest.json`
- `channel-manifest.json`

The application never switches channel silently. A build created for `stable` reads only the stable update path; a beta build reads only beta.

## 4. Local production build

```powershell
$env:CAF_INO_LICENSE_PUBLIC_KEY_PATH="C:\secure\cafino\license-public-key.pem"
$env:CAF_INO_UPDATE_URL="https://updates.example.com/cafino/local/stable"
$env:CSC_LINK="C:\secure\cafino\codesign.pfx"
$env:CSC_KEY_PASSWORD="..."

.\scripts\build-release.ps1 -Production -Channel stable
```

For beta:

```powershell
.\scripts\build-release.ps1 -Production -Channel beta
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
- channel update feed generated

Artifacts are under `electron/release/`; deployable feed is under `electron/release/publish/<channel>/`.

## 5. GitHub Actions production release

Workflow: `Cafino Local Production Release`.

Required repository secrets for every signed build:

- `CAF_INO_UPDATE_BASE_URL`
- `CAF_INO_LICENSE_PUBLIC_KEY_PEM`
- `CSC_LINK`
- `CSC_KEY_PASSWORD`

Workflow inputs:

- `version`
- `channel`: `stable` or `beta`
- `publish_update_feed`: false by default

Stable rejects prerelease SemVer values. Beta accepts normal SemVer or prerelease SemVer such as `1.3.0-beta.1`.

The workflow performs:

1. Production build.
2. Signed release-manifest validation.
3. Authenticode validation.
4. Silent NSIS install on a clean Windows GitHub runner.
5. Packaged runtime `--cafino-smoke-check`.
6. Silent uninstall when available.
7. Upload of the verified release bundle as a GitHub Actions artifact.
8. Optional publish to S3-compatible storage.

A release that fails smoke testing is never published by this workflow.

## 6. S3-compatible CDN publication

Publication is intentionally storage-provider-neutral and works with AWS S3, Cloudflare R2, and compatible object-storage services.

Required secrets when `publish_update_feed=true`:

- `CAF_INO_UPDATE_ACCESS_KEY_ID`
- `CAF_INO_UPDATE_SECRET_ACCESS_KEY`
- `CAF_INO_UPDATE_BUCKET`
- `CAF_INO_UPDATE_REGION` — optional when provider does not require it
- `CAF_INO_UPDATE_ENDPOINT` — optional custom S3 API endpoint, typically used by R2 or other compatible providers

The workflow syncs only the verified directory:

```text
electron/release/publish/<channel>/
```

to:

```text
s3://<bucket>/<channel>/
```

The public HTTPS host represented by `CAF_INO_UPDATE_BASE_URL` must map those same channel paths to the bucket.

Before enabling publish, verify that the public endpoint serves `latest.yml` and the installer over HTTPS without authentication.

## 7. Customer offline activation

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

## 8. Backup policy

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

Backups use the verified SQLite flow and are pruned only after a successful backup.

## 9. Safe update flow

1. Cafino checks only its configured channel HTTPS endpoint.
2. Operator downloads the update from Settings → Release & License.
3. Before installation, Cafino creates and verifies a `pre-update` database backup.
4. An update recovery journal records current version, target version, backup path and backup hash.
5. The NSIS updater installs and restarts Cafino.
6. New runtime must pass backend health verification.
7. If health verification fails, the recovery journal is marked `recovery_required` and the pre-update backup is preserved.

## 10. Rollback boundary

Database rollback and binary rollback are deliberately separate.

If a new binary is unhealthy:

1. Do **not** silently restore an old database while continuing to run the new binary.
2. Reinstall the previous signed Cafino installer.
3. Restore the pre-update database backup from Backup/Restore.
4. Re-run Go-Live / Local Runtime Preflight.

Keep at least one previous signed installer available for each production channel.

## 11. Release acceptance

A production release should not be delivered unless:

- CI is green.
- Signed installer is built.
- Authenticode status is valid.
- clean-Windows silent install passes.
- packaged smoke check passes.
- release manifest hashes are retained.
- update endpoint serves matching metadata and artifacts.
- license activation is tested on a real target Windows machine before broad rollout.
- backup → restore drill passes on the target device.
- previous signed installer is retained for rollback.

The GitHub runner smoke test proves packaging/installability. It does not replace a pilot rollout on one real customer device with the actual printer/POS/pager hardware profile.
