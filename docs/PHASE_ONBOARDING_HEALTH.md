# Cafino — Onboarding & Health phase

This phase makes first-run business setup self-service while keeping business rules and readiness checks server-authoritative.

## Onboarding presets

Cafino ships code-defined presets for Cafe, Restaurant, Fast Food, Bakery, Pastry, Catering and Hotel Restaurant. Applying a preset:

- updates business type and deployment model;
- creates explicit BusinessModule states for the full known module catalog when replace mode is selected;
- can create a default cash register;
- can bootstrap a hall and numbered tables;
- can create suggested preparation stations;
- can ensure initial online-menu settings;
- never fabricates real products, prices, recipes, inventory or accounting data;
- writes an `ONBOARDING_PRESET_APPLIED` AuditLog entry.

Preset application requires both `settings.manage` and `business.manage`.

## Settings health checks

`GET /api/v1/settings/health/?branch=<id>&live=0|1` distinguishes configuration/application/network/hardware checks for:

- online menu;
- SMS provider;
- payment gateway;
- printer configuration.

Live network probes use HEAD only and never create a payment or send an SMS. Redirect following is disabled. Server deployments reject private, loopback, link-local, multicast, reserved and unspecified targets to reduce SSRF exposure. Local deployment may probe private network endpoints.

`POST /api/v1/settings/health/printer/` compares configured printer system names with device names discovered by Cafino Desktop/Electron.

## Frontend

`/settings/onboarding` provides a four-step RTL wizard:

1. choose the business preset;
2. choose branch and deployment model;
3. choose safe bootstrap options;
4. review readiness and run configuration/live/local-printer health checks.

The existing Settings Overview and sidebar link to the wizard only for users with `business.manage`.
