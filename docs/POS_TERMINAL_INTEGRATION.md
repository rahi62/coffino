# Cafino Local POS/Card Terminal Integration

Cafino treats payment terminals as a **Local hardware boundary**. The SaaS browser never receives PSP secrets and does not attempt USB/serial/Windows-SDK access.

## Current behavior

`MANUAL` remains the default adapter. In this mode Cafino records a POS payment only after the operator has completed the terminal transaction manually, exactly as before.

When a direct adapter is selected in Cafino Local, the frontend checkout path asks Electron to authorize the POS amount **before** sending the checkout request to Django. A declined/failed terminal result blocks order/payment creation. On approval, `RRN/reference_number` is sent to Django and persisted on `Payment.reference_number`.

The checkout `Idempotency-Key` is also used to create the terminal request reference. Vendor bridges MUST treat this reference as idempotent so retrying a checkout after a network/API failure cannot charge the card twice.

For safety, automatic direct-terminal authorization currently supports at most **one POS tender per checkout**. Mixed Cash + one POS tender is supported. Multiple direct POS tenders in one checkout are blocked until a two-phase multi-tender reconciliation flow is introduced.

## Adapter choices

Set one of:

```text
CAF_INO_POS_ADAPTER=MANUAL
CAF_INO_POS_ADAPTER=HTTP_BRIDGE
CAF_INO_POS_ADAPTER=TCP_JSON
CAF_INO_POS_ADAPTER=EXEC_BRIDGE
CAF_INO_POS_ADAPTER=VENDOR_SDK
```

`VENDOR_SDK` is intentionally `planned`: it is implemented only after the exact PSP/terminal SDK is known. In practice, HTTP/TCP/EXEC bridges let us integrate most Windows SDKs without coupling Cafino Core to a bank vendor library.

Legacy `CAFINO_POS_ADAPTER` is still accepted for adapter selection.

## Amount unit

Cafino prices/payments are stored in **Rial**.

Default:

```text
CAF_INO_POS_AMOUNT_UNIT=RIAL
```

If a vendor SDK expects Toman:

```text
CAF_INO_POS_AMOUNT_UNIT=TOMAN
```

Toman mode divides the Cafino Rial amount by 10 and refuses values that are not exactly divisible by 10. Never hide currency conversion inside a vendor bridge.

## HTTP bridge

Configuration:

```text
CAF_INO_POS_ADAPTER=HTTP_BRIDGE
CAF_INO_POS_BRIDGE_URL=http://127.0.0.1:17890/sale
CAF_INO_POS_BRIDGE_TOKEN=<optional-local-shared-token>
CAF_INO_POS_TIMEOUT_MS=90000
```

For security, Cafino accepts bridge URLs only on localhost/RFC1918 private addresses by default. If a trusted local hostname is required:

```text
CAF_INO_POS_BRIDGE_ALLOW_HOSTS=pos-agent.local
```

Request:

```json
{
  "amount": 1250000,
  "currency": "IRR",
  "reference": "<checkout-idempotency-key>:pos:0",
  "payer_label": "نفر ۱"
}
```

The bridge should return JSON. Cafino understands common names such as:

```json
{
  "status": "approved",
  "rrn": "123456789012",
  "trace": "654321",
  "terminal_id": "12345678",
  "masked_pan": "****1234",
  "message": "approved"
}
```

`approved=true`, `ok=true`, `success=true`, or a status of `approved/success/succeeded/ok/00` is treated as approval.

Cafino never needs the full PAN or PIN. Even if a bridge mistakenly returns a full PAN, only the last four digits are retained in the Electron response and they are not stored in the Django Payment model.

## TCP JSON bridge

Configuration:

```text
CAF_INO_POS_ADAPTER=TCP_JSON
CAF_INO_POS_TCP_HOST=127.0.0.1
CAF_INO_POS_TCP_PORT=17891
CAF_INO_POS_TIMEOUT_MS=90000
```

Protocol:

1. Cafino opens one TCP connection.
2. Sends one JSON object followed by `\n` using the same request fields as HTTP.
3. Reads one JSON response line.
4. Closes the connection.

This is intended for a local companion process. Do not expose this TCP port publicly.

## Vendor executable bridge

This is usually the fastest integration when a PSP provides a Windows DLL/EXE or .NET SDK.

```text
CAF_INO_POS_ADAPTER=EXEC_BRIDGE
CAF_INO_POS_EXECUTABLE=C:\Program Files\CafinoPOSBridge\cafino-pos-bridge.exe
CAF_INO_POS_TIMEOUT_MS=90000
```

Cafino invokes it with `execFile` (no shell):

```text
cafino-pos-bridge.exe --amount 1250000 --currency IRR --reference <reference>
```

The executable writes exactly one JSON response to stdout using the response contract above.

The helper can internally load the vendor DLL/.NET SDK/COM component. This keeps vendor-specific binaries outside the Cafino domain layer and makes upgrades/testing safer.

## What is needed for a specific terminal

Send these when the real terminal is selected:

- PSP/provider name (for example Behpardakht, Saman Kish, Iran Kish, Pasargad, etc.).
- terminal brand/model.
- connection type: LAN, USB, serial, COM, local service, vendor EXE/DLL.
- vendor integration manual/protocol.
- SDK files or installer and sample project if supplied by the provider.
- whether the terminal expects Rial or Toman.
- sale response fields and cancellation/reversal API if supported.

Do **not** send real PINs, card numbers, production merchant secrets or private keys in chat/repository. Test credentials can be configured locally through environment/secret storage.

## Acceptance test for a real terminal

1. Select/configure the adapter.
2. Settings → Go-Live / Local preflight must show the POS adapter as ready.
3. Create a small single-POS checkout.
4. Cafino sends the exact final amount after discount/tax/service.
5. Cancel/decline at terminal: no Django Payment/order checkout should be created by that request.
6. Approve: order is created and Payment has the terminal RRN/reference.
7. Retry the same checkout reference: bridge must return the existing terminal result, not charge again.
8. Disconnect terminal/network: Cafino shows a terminal error and does not silently mark payment successful.
9. Verify receipt/payment report and daily close.

## Next vendor-specific step

The generic integration layer is complete enough to start now. The only vendor-specific work remaining is a small bridge/adapter that translates the selected PSP SDK protocol to the contract documented here.
