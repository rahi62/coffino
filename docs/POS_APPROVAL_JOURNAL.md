# Cafino POS Approval Journal

Cafino Local keeps a small append-only approval journal for direct card-terminal payments. Its purpose is to prevent a second terminal Sale when the bank approved the first attempt but the Django checkout request failed or had to be retried.

## Rules

- Every automatic terminal Sale requires a stable checkout/idempotency reference.
- An approved reference is written to the local journal before Cafino treats it as safely reusable.
- Retrying the same reference and same Cafino Rial amount returns the previously approved result without calling the terminal bridge again.
- Reusing the same reference with another amount is blocked.
- Concurrent calls using the same reference are coalesced in-process so only one terminal Sale can be in flight.
- Declined/failed transactions are not journaled; the customer may retry the same checkout after a decline.
- The journal stores only sanitized approval fields: amount, RRN/reference, trace, terminal id and masked PAN. Full PAN/PIN/merchant secrets are never stored.
- The file is append-only NDJSON so an already committed approval is not rewritten during normal operation.

Default Windows location is under `%APPDATA%/Cafino/pos-approvals.ndjson`. For testing or managed installations it can be overridden with:

```text
CAF_INO_POS_JOURNAL_PATH=C:\ProgramData\Cafino\pos-approvals.ndjson
```

## Failure policy

Automatic POS fails closed if the existing journal is structurally unreadable. Do not delete or replace a damaged journal until its RRN/trace entries have been reconciled with the terminal/PSP and Cafino payments.

If the bank approves a transaction but the approval cannot be persisted, Cafino returns an `approved_journal_error`, keeps the sanitized approval in process memory, and tells the operator not to restart or create a new payment. The RRN/trace must be reconciled before continuing.

## Why the vendor bridge still needs idempotency

The Cafino journal protects retries after Cafino has received a confirmed approval. The PSP/vendor bridge must also treat the supplied `reference` as idempotent because the transport can fail after the terminal/PSP processed the Sale but before Cafino received the response. A status-query/reversal API from the real provider is required for final hardware certification.
