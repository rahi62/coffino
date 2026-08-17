# Cafino Local — Update Feed Operations

This document defines the production update-feed contract for Cafino Local Windows releases.

## Architecture

Cafino source code remains in the private GitHub repository. Customer installations do not receive GitHub credentials.

Production updates use an HTTPS generic `electron-updater` feed hosted on a public-read S3-compatible bucket/CDN.

Recommended public URL layout:

```text
https://updates.example.com/cafino/local/stable/
https://updates.example.com/cafino/local/beta/
```

Object storage layout must match the public URL path:

```text
cafino/local/stable/
cafino/local/beta/
```

The default object prefix is `cafino/local` and can be changed with the repository variable `CAF_INO_UPDATE_PREFIX`.

## Channels

Cafino supports two release channels:

- `stable` — production users. Package version must be plain SemVer such as `1.2.0`. Update metadata is `latest.yml`.
- `beta` — pilot/test users. Package version must contain `-beta`, such as `1.3.0-beta.1`. Update metadata is `beta.yml`.

A build is permanently bound to its feed URL through the packaged release configuration:

```text
stable build -> <base-url>/stable
beta build   -> <base-url>/beta
```

The Electron updater infers the update channel from the feed URL and does not permit downgrade installation automatically.

## Required GitHub secrets

### Build and signing

```text
CAF_INO_UPDATE_BASE_URL
CAF_INO_LICENSE_PUBLIC_KEY_PEM
CSC_LINK
CSC_KEY_PASSWORD
```

`CAF_INO_UPDATE_URL` is accepted only as a legacy fallback. New configuration should use `CAF_INO_UPDATE_BASE_URL` without `/stable` or `/beta`.

Example:

```text
CAF_INO_UPDATE_BASE_URL=https://updates.example.com/cafino/local
```

### S3-compatible publication

```text
CAF_INO_UPDATE_ACCESS_KEY_ID
CAF_INO_UPDATE_SECRET_ACCESS_KEY
CAF_INO_UPDATE_REGION
CAF_INO_UPDATE_BUCKET
```

Optional:

```text
CAF_INO_UPDATE_ENDPOINT
```

Set `CAF_INO_UPDATE_ENDPOINT` for providers such as Cloudflare R2, Backblaze B2 S3, MinIO, or another S3-compatible endpoint. Leave it empty for standard AWS S3.

Optional repository variable:

```text
CAF_INO_UPDATE_PREFIX=cafino/local
```

## Production workflow

GitHub Actions workflow:

```text
Cafino Local Production Release
```

Inputs:

- `version`
- `channel`: `stable` or `beta`
- `publish`: whether the verified bundle should be pushed to the update feed

The workflow performs these stages:

1. Validate version/channel compatibility.
2. Build backend, frontend and Electron release.
3. Require Windows code signing.
4. Verify the final installer with `Get-AuthenticodeSignature`.
5. Require channel metadata (`latest.yml` or `beta.yml`).
6. Store installer, metadata, blockmap and SHA-256 release manifest as a GitHub Actions artifact.
7. If `publish=true`, upload immutable binary artifacts first.
8. Upload `release-manifest.json`.
9. Upload update metadata **last**.
10. Verify that the metadata is reachable from the public HTTPS feed.

## Why metadata is uploaded last

`latest.yml` / `beta.yml` is the pointer used by installed clients to discover a new release. Publishing it before the installer or blockmap could make clients discover an update that is not yet fully available.

The publication workflow therefore uses this order:

```text
installer -> blockmap -> manifest -> metadata
```

Old installers are not deleted. They are retained for rollback and forensic comparison.

## Cache policy

Installer and blockmap:

```text
Cache-Control: public,max-age=31536000,immutable
```

Release manifest:

```text
Cache-Control: no-cache
```

Channel metadata:

```text
Cache-Control: no-cache,no-store,must-revalidate
```

This allows large immutable binaries to be cached while ensuring clients see current update metadata.

## Bucket/CDN requirements

The public update origin must:

- serve HTTPS only;
- allow unauthenticated GET/HEAD for published update objects;
- preserve filenames exactly;
- serve the installer and metadata from the same channel directory;
- not rewrite `latest.yml` / `beta.yml` into HTML;
- support binary downloads without content transformation;
- retain old installers unless an explicit retention process archives them elsewhere.

The object-storage write credentials belong only in GitHub Actions secrets. They must never be packaged into Cafino.

## Installed Windows smoke test

Workflow:

```text
Cafino Windows Installed Smoke
```

The smoke workflow builds a full Local release, installs the NSIS package silently into a clean temporary path, launches the installed `Cafino.exe`, and verifies:

```text
http://127.0.0.1:8000/api/v1/health/
http://127.0.0.1:3000/
```

It also verifies that the NSIS uninstaller was installed.

This test intentionally uses a non-production unsigned build so it can exercise the installed backend/frontend runtime without requiring a customer license or production certificate.

## Production acceptance checklist

Before making a stable release visible to customers:

- all normal CI jobs are green;
- Windows Installed Smoke is green;
- Production Release build completes with a valid Authenticode signature;
- `release-manifest.json` exists;
- `latest.yml` exists for Stable or `beta.yml` exists for Beta;
- public metadata verification passes;
- the release URL matches the intended channel;
- offline license issuance/import has been tested on a clean Windows device;
- a pre-update backup/restore drill has passed;
- the previous signed installer remains available for rollback.

## Current known release asset gap

The repository currently does not contain a Cafino Windows `.ico` brand asset. Until a real icon is supplied and wired into electron-builder, Windows packaging uses the default Electron application icon. Do not treat the visual installer branding as final until this asset is added.
