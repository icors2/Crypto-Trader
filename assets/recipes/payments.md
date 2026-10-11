# Recipe: Payments

**Sensitive:** yes — `security-review` required. Never put live secret keys in the client.

## Goal

User can complete one successful test-mode checkout (or subscription create) and a webhook updates app state.

## Defaults (if unset)

- Stripe (Checkout Session or Payment Element). Use test keys locally.

## Minimum slice

1. Env names: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, publishable key if needed.
2. Server route creates Checkout Session / PaymentIntent.
3. Success and cancel URLs wired.
4. Webhook endpoint verifies signature and updates one domain record (e.g. `order.status`).

Out of scope for v1: tax, invoices UI, customer portal polish, multi-currency edge cases — unless asked.

## Security

- Secret key and webhook secret **only** on the server — including **test-mode** secrets. Client may use the **publishable** key only.
- Verify webhook signatures using the **raw request body** (e.g. Stripe `constructEvent`). Never disable verification to unblock local testing.
- Idempotent webhook handling (Stripe may retry).
- Server owns amounts / price IDs from a trusted catalog; do not trust client-supplied prices.
- Do not trust client-reported "paid" without webhook or PaymentIntent retrieve.

## Verify

- Test-mode payment succeeds
- Webhook marks the record paid (use Stripe CLI or dashboard test)
- `security-review` on payment routes

## MCP

`stripe` from the catalog when useful for the agent.
