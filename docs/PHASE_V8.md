# Cafino v8 — Customer Experience + Advanced Operations

## Scope delivered

### Item-level Split Bill
- DINE_IN/POS can create an unpaid order and send it to preparation.
- BillSplit and BillSplitLine allocate quantities of each OrderItem to named payers.
- Every ordered quantity must be allocated exactly once before Split creation succeeds.
- Discount, tax, service charge and final grand total are allocated with rounding reconciliation.
- Each split can be settled using its own mixed tender; Payment rows remain attached to the original Order and optionally the BillSplit.
- Refunds update affected split status.

### Lot / Expiry / FEFO inventory
- InventoryItem supports `lot_tracked` and shelf-life metadata.
- InventoryLot stores lot number, received/remaining quantity, cost, source and expiry.
- Purchase and Production can create lots.
- Sale, production consumption, waste and inter-branch transfers use a common Lot-aware stock service.
- Non-expired, non-blocked lots are consumed in FEFO order.
- Expired/blocked lots are not silently consumed.
- OrderItem COGS snapshot is now derived from the lots actually consumed.
- Void restores inventory to the same consumed lots.
- Existing stock can be bootstrapped into a `LEGACY-*` lot when Lot Tracking is enabled.
- Aggregate physical-count adjustment on Lot-tracked items is rejected because a lot-level discrepancy must be resolved explicitly.

### Reservations
- Reservation model with time, duration, table, party size, source and lifecycle.
- Conflict validation for overlapping reservations on the same table.
- Seating a reservation creates a real TableSession.
- Closing a table session preserves RESERVED status when a future reservation exists.

### Customer Loyalty + Wallet
- Branch LoyaltyProgram.
- Customer points account and append-only loyalty ledger.
- Wallet account and wallet transaction ledger.
- Points are earned once when an identified customer's order is completed.
- Points can be converted to wallet credit using branch rules.
- WALLET is now a real payment method that debits customer balance transactionally.
- WALLET refund credits the customer's wallet.

### Notification Center + SMS queue
- Notification domain for IN_APP and SMS.
- ORDER_READY creates deduplicated notifications.
- Generic HTTP SMS adapter with configurable endpoint, headers, sender and field names.
- SMS API keys are encrypted at rest using Fernet derived from Django SECRET_KEY.
- Retry/backoff state is persisted.
- Manual processing API and `python manage.py process_notifications` command.
- Local operations are never blocked by SMS/provider failure.

### QR / Online Ordering
- Per-branch OnlineMenuSettings and public slug.
- Per-table UUID QR token.
- Public menu endpoint and public Next.js menu page do not require staff login.
- QR table order attaches to/open a TableSession.
- PAY_AT_COUNTER creates the normal kitchen/inventory workflow with UNPAID Order.
- ONLINE creates a pending online Payment and holds inventory/KDS fulfillment until payment confirmation.
- Provider-specific gateway adapters can call the `confirm_online_payment` service.
- Public order-status polling updates the customer page.
- Local SVG QR generation uses the Python `qrcode` package.

## Safety invariants
- Core POS remains usable without customer internet, SMS provider or online-ordering services.
- Online payment pending orders do not consume stock or enter KDS before confirmation.
- FEFO never consumes expired or blocked lots.
- Wallet debit/refund and payment rows share one DB transaction.
- Split Bill cannot be created after payment has started.
- Notification retries are deduplicated and do not create duplicate ORDER_READY messages.

## Still intentionally adapter-dependent
- A real online payment gateway is not fabricated. The v8 core exposes a pending Payment + confirmation service for the selected PSP adapter.
- SMS payload is generic HTTP; each provider may require a small provider-specific adapter/config.
- Hardware pager integrations remain vendor-specific adapters.

## Next candidates
- Lot-level physical counts and FEFO transfer UX with lot selection/traceability.
- Item transfer between open checks/tables and order merge.
- Gift cards, customer tiers/campaigns and coupon targeting.
- Real PSP adapter/webhook and online payment reconciliation.
- Delivery zones/courier dispatch.
- Customer PWA installability, push notifications and offline menu cache.
