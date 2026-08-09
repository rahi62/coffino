# Cafino Architecture
Cafino order-centric است، نه invoice-centric.

Order -> Payment -> Preparation -> Fulfillment -> Receipt

برای کافه‌های پرداخت‌اول، UI یک عملیات سریع «پرداخت و ارسال به آماده‌سازی» دارد ولی Order/Payment/KitchenTicket در دامنه جدا می‌مانند.

Deployment:
- Local: Electron + Django Local + DB Local
- SaaS: Multi-tenant Cloud
- Dedicated: Single-tenant managed

## Financial operations implemented in v4

- Multi-line purchase invoice posts inventory movements atomically.
- Supplier balance = opening balance + posted purchases - supplier payments.
- Cash supplier payments create cash-drawer movements; non-cash methods do not.
- Cash expenses create cash-drawer movements.
- Cash sales create SALE cash movements automatically; POS sales do not affect the physical cash drawer.
- Order Void restores recipe inventory and reverses recorded payments. For completed orders, use Refund instead of Void.
- Refund is a separate auditable record and reduces net sales in management reporting.
- Profit dashboard uses net revenue, recipe-based COGS, operating expenses and normalized monthly overhead.
- Break-even is estimated from average order value and contribution per order. It is a managerial estimate, not statutory accounting.
