# Cafino v7 — Inventory Control, Multi-Branch Operations & Advanced Checkout

## Delivered

### Inventory Control
- Physical inventory counts with system snapshot, counted quantity, variance and cost variance.
- Posting a count writes `ADJUSTMENT` stock movements.
- Safety lock: if stock changes after the count snapshot, posting is rejected instead of overwriting live movements.
- Atomic inter-branch stock transfer with `TRANSFER_OUT` + `TRANSFER_IN`.
- Transferred inventory carries cost and destination weighted-average cost is recalculated.

### Production / Bakery
- ProductionFormula and ingredient rows.
- ProductionBatch with multiplier, batch number, actual ingredient cost snapshots and expiry timestamp.
- Posting a batch consumes ingredients and adds finished goods to inventory.
- Products can optionally point to a finished-goods `stock_item`; those products consume finished inventory at sale time instead of raw recipes.
- Recipe-driven café products continue to consume ingredients directly.

### Fiscal Pricing
- Per-branch FiscalSettings.
- Tax, service charge, prices-including-tax mode and service-charge order-type policies.
- Tax/service/discount totals are snapshotted on the Order before payment.
- Management revenue excludes tax collected.
- Refunds proportionally reduce recognized tax/revenue.
- Service charge can be configured as revenue or pass-through.

### Advanced Checkout
- One Order can have multiple Payments.
- CASH, POS, ONLINE, CREDIT, WALLET and GIFT_CARD methods.
- Equal split by guest count and arbitrary mixed-payment rows.
- Payer labels are stored on Payment rows.
- Cash tender/change fields.
- Mixed-payment refunds allocate across refundable original Payments.
- CashMovement is generated only for cash tender/refund portions.

### Checkout Safety
- Backend checkout preview is the source of truth for discount, service charge, tax and final amount.
- Direct mutation of Order financial fields is blocked.
- Direct Payment/Refund CRUD is read-only; money flows through checkout/settle/refund services.
- Per-branch order numbering is serialized by locking Branch during checkout.
- Idempotency-Key + payload fingerprint protects retry/double-click behavior.

### Printing
- PrinterDevice, PrintTemplate and PrintJob domain.
- Receipt and kitchen payload generation.
- Electron enumerates OS-installed printers and performs actual silent printing through `webContents.print()`.
- Receipt and kitchen PrintJobs record printed/failed states.
- Raw vendor-specific ESC/POS remains an adapter concern for later hardware integrations.

### Reporting
- KPI dashboard:
  - Net revenue
  - Average ticket
  - Gross margin %
  - Food Cost %
  - Waste
  - Refund rate
  - Labor hours
  - Sales per labor hour
  - Cash variance
  - Break-even
  - Low-stock count
  - Top product

## Important limitations

1. Current Split Bill is amount/payer split on one Order. Item-by-item bill allocation is not implemented yet.
2. Production Batch has an expiry timestamp but inventory is not yet lot-level/FEFO.
3. OS-driver printing is implemented. Brand-specific raw ESC/POS, cash drawer kick and proprietary printer SDKs are separate adapters.
4. Current local development database is SQLite; production SaaS/Dedicated should use PostgreSQL.
5. Migrations must be generated after dependencies are installed because the artifact-build environment does not include Django.

## Demo data

`python manage.py seed_demo`

- admin / admin1234
- Manager PIN: 4321
- cashier / cashier1234
- discount code: VIP10
- two branches
- bakery finished-good + production formula
- DINE_IN service-charge fiscal sample
