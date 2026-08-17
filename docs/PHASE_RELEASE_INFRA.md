# Cafino — Real Production Release Infrastructure

This phase extends the Local release pipeline beyond installer creation into channelized, smoke-tested and optionally published production updates.

## Delivered

- Stable and Beta release channels.
- Channel-specific HTTPS update URLs.
- Deterministic static update-feed bundle under `electron/release/publish/<channel>/`.
- SHA-256 `release-manifest.json` plus per-channel `channel-manifest.json`.
- Explicit packaged `--cafino-smoke-check` mode that validates packaged backend, frontend, release configuration, channel, HTTPS update URL and public license key presence without weakening normal license enforcement.
- Silent NSIS install/uninstall smoke test on Windows.
- Production workflow blocks publication until Authenticode and packaged smoke checks pass.
- Optional S3-compatible publishing for AWS S3, Cloudflare R2 or compatible object stores.
- CI installer contract now installs the generated NSIS package and runs the packaged smoke check.

## Operational boundary

Actual production publication still requires repository secrets for the real signing certificate, public license key, public HTTPS update base URL and, when publication is enabled, object-storage credentials. Those are intentionally not committed to the repository.

The CI installer contract uses an unsigned development package only to prove packaging/installability. The manual production workflow requires a trusted Authenticode signature before it can proceed to publish.
