# Cafino v6 — Operational Control

## Delivered
- Permission Matrix UI with role inheritance and per-user allow/deny overrides.
- Manager PIN stored with Django password hashing.
- Two-minute signed override tokens scoped to branch + permission.
- Manual discounts evaluated before Payment.
- Discount Rule Engine: auto/code, order/category/product scope, percent/fixed, min order, cap, date range, weekdays, priority and manager requirement.
- Staff scheduling and clock-in/clock-out attendance.
- Waste registration that decrements inventory and writes StockMovement + AuditLog.
- Historical `OrderItem.unit_cost_snapshot` for stable COGS.
- Food Cost dashboard: theoretical consumption, waste, operational food cost %, top waste.
- Multi-branch management dashboard.
- Permission-aware navigation.
- Daily closing expected cash based on CashMovement ledger.

## Financial invariants
- Paid order totals are never mutated by a late discount.
- Post-payment monetary corrections use Refund.
- Void and Refund are separate workflows.
- COGS snapshots are captured when the order is created.
- Waste stores a cost snapshot at the time of waste.
- Manager override tokens are short-lived and permission-scoped.
- Sensitive changes are sent to AuditLog.

## Demo
`seed_demo` creates:
- admin / admin1234
- demo manager PIN: 4321
- cashier / cashier1234
- automatic discount rule
- VIP10 code
- a second branch for comparison

Demo credentials are for local development only.

## Next production hardening
- Generate and commit migrations after installing dependencies.
- Database-level append-only protection/hash chain for AuditLog.
- Branch-aware selector/policy layer across every legacy ViewSet.
- Receipt discount breakdown per item for tax-grade allocation.
- Overtime/payroll rules.
- Inventory physical-count variance workflow.
