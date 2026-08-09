# Phase V5 — Control, audit and operational reporting

Implemented:
- Append-only AuditLog model/service for sensitive actions
- Role + permission override foundation
- Manager approval workflow for discount and void
- Daily financial closing snapshot
- Item/category/hour sales analytics
- Cashier performance report
- JWT authentication enabled in DRF settings

Security/financial rules:
- Cashiers request privileged discount/void; managers/owners approve.
- Daily closing is immutable by API (read-only viewset).
- Audit API is read-only.
- Void and refund remain separate domain operations.
- Reports exclude cancelled orders and subtract refunds where applicable.

Next hardening:
- DB-level append-only protection for AuditLog
- cryptographic hash chain for audit records
- configurable discount thresholds per business
- approval PIN / second-device approval
- timezone-aware business-day cutoff
- legal double-entry accounting module
