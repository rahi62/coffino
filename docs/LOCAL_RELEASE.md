# Cafino Local — Production Release Runbook

This runbook covers the Windows Local edition only. The production build is intentionally stricter than a development/unsigned build.

For update-feed storage/CDN details, also read `docs/UPDATE_FEED.md`.

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

Do not commit signing credentials. The production script refuses to continue without them unless `-AllowUnsigned` is explicitly used for a non-production/pilot validation build.

The GitHub Production Release workflow additionally checks the final installer with `Get-AuthenticodeSignature` and rejects a non-valid signature.

## 3. Update endpoint and channels

Cafino Local uses `electron-updater` with the NSIS target and a generic HTTPS update endpoint.

Set the base URL without a channel suffix:

```powershell
$env:CAF_INO_UPDATE_BASE_URL="https://updates.example.com/cafino/local"
```

The build script derives one of these URLs:

```text
https://updates.example.com/cafino/local/stable
https://updates.example.com/cafino/local/beta
```

Channel rules:

- Stable: plain SemVer such as `1.2.0`; metadata `latest.yml`.
- Beta: prerelease SemVer such as `1.3.0-beta.1`; metadata `beta.yml`.

`CAF_INO_UPDATE_URL` remains supported only as a legacy fallback. New deployments should use `CAF_INO_UPDATE_BASE_URL`.

The update directory must serve the installer, matching update metadata and blockmap generated from the same build.

## 4. Production build

Stable example:

```powershell
$env:CAF_INO_LICENSE_PUBLIC_KEY_PATH="C:\secure\cafino\license-public-key.pem"
$env:CAF_INO_UPDATE_BASE_URL="https://updates.example.com/cafino/local"
$env:CSC_LINK="C:\secure\cafino\codesign.pfx"
$env:CSC_KEY_PASSWORD="..."

.\scripts\build-release.ps1 -Production -Channel stable
```

Beta example requires the Electron package version to include `-beta`:

```powershell
.\scripts\build-release.ps1 -Production -Channel beta
```

Production build gates:

- static release contract
- version/channel compatibility
- no migration drift
- migrations apply
- Django deployment checks
- full backend tests
- PyInstaller backend build
- Next.js production build
- Electron release tests
- NSIS installer build
- Windows signing required
- channel metadata generated (`latest.yml` or `beta.yml`)
- SHA-256 release manifest generated

Artifacts are under `electron/release/`.

## 5. GitHub Actions signed build and publication

Workflow: `Cafino Local Production Release`.

Build/signing secrets:

- `CAF_INO_UPDATE_BASE_URL`
- `CAF_INO_LICENSE_PUBLIC_KEY_PEM`
- `CSC_LINK`
- `CSC_KEY_PASSWORD`

Optional S3-compatible publication requires:

- `CAF_INO_UPDATE_ACCESS_KEY_ID`
- `CAF_INO_UPDATE_SECRET_ACCESS_KEY`
- `CAF_INO_UPDATE_REGION`
- `CAF_INO_UPDATE_BUCKET`
- optional `CAF_INO_UPDATE_ENDPOINT`

Optional repository variable:

- `CAF_INO_UPDATE_PREFIX` — defaults operationally to `cafino/local`

Run the workflow manually and choose:

- `version`
- `channel`: Stable or Beta
- `publish`: false to only build/verify the bundle, true to publish it

When publication is enabled, immutable binaries are uploaded first and channel metadata is uploaded last. The workflow then verifies the public HTTPS metadata URL.

The source repository may remain private; customer applications consume only the public update feed and never require GitHub credentials.

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

1. Cafino checks the HTTPS feed packaged for its release channel.
2. Operator downloads the update from Settings → Release & License.
3. Before installation, Cafino creates and verifies a `pre-update` database backup.
4. An update recovery journal records current version, target version, backup path and backup hash.
5. The NSIS updater installs and restarts Cafino.
6. New runtime must pass backend health verification.
7. If health verification fails, the recovery journal is marked `recovery_required` and the pre-update backup is preserved.

Automatic downgrade is disabled. Moving a customer between Stable and Beta should be an explicit deployment decision rather than an implicit updater downgrade.

## 9. Rollback boundary

Database rollback and binary rollback are deliberately separate.

If a new binary is unhealthy:

1. Do **not** silently restore an old database while continuing to run the new binary.
2. Reinstall the previous signed Cafino installer.
3. Restore the pre-update database backup from Backup/Restore.
4. Re-run Go-Live / Local Runtime Preflight.

Keep previous signed installers available in update storage or an immutable release archive.

## 10. Clean Windows installed smoke

Workflow: `Cafino Windows Installed Smoke`.

It builds a full non-production Local installer, installs it silently into a clean temporary path, launches the installed application and verifies:

```text
http://127.0.0.1:8000/api/v1/health/
http://127.0.0.1:3000/
```

It also verifies that the NSIS uninstaller exists. This catches integration failures that source-level backend/frontend tests and a stub installer contract cannot detect.

## 11. Release acceptance

A production Stable release should not be delivered unless:

- normal CI is green;
- Windows Installed Smoke is green;
- signed installer is built and Authenticode reports `Valid`;
- release manifest hashes are stored with the release;
- update endpoint serves matching metadata/artifacts;
- public feed verification passes;
- license activation is tested on a clean Windows machine;
- backup → restore drill passes on the target device;
- previous signed installer is retained for rollback.

## 12. Known visual packaging gap

The repository currently has no Cafino Windows `.ico` asset. electron-builder therefore uses its default Electron icon. Before commercial distribution, add the approved Cafino brand icon and wire it into the Windows builder configuration.
