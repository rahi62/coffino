# Phase 3 — Three-mode responsive UI

Cafino now uses three operational responsive modes instead of a desktop layout with a phone-only patch.

| Mode | Width | Navigation | POS |
|---|---:|---|---|
| Mobile | < 768px | top bar + drawer | full-width menu + bottom cart sheet |
| Tablet | 768–1279px | 76px icon rail + full drawer | category row + menu/cart split |
| Desktop | >= 1280px | full labelled sidebar | category/menu/cart three-pane layout |

## Scope

- App shell spacing follows the three breakpoints.
- Tablet uses a persistent icon rail.
- Mobile and tablet retain the full navigation drawer.
- Existing /operations navigation is preserved.
- POS checkout/payment/business logic is unchanged; only responsive presentation changed.
- Mobile POS uses a bottom cart sheet with safe-area-aware actions.
- Touch targets are enlarged on coarse-pointer devices.
- Phone inputs use 16px text to avoid iOS zoom-on-focus.
- Existing mobile.css remains loaded.

## Regression checks

- scripts/responsive-contract.js is the static CI contract.
- scripts/responsive-audit.py is an optional Playwright browser audit.
- Audit viewports: 390x844, 820x1180, 1180x820, 1440x900.

## Remaining real-device QA

- iOS Safari safe areas and keyboard behavior.
- Android Chrome touch behavior.
- Phone landscape.
- Full checkout/payment flow from the mobile cart sheet.
- Dense data tables on small screens.
- Public menu /menu/[slug].
