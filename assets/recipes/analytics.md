# Recipe: Analytics

**Sensitive:** medium — minimize PII; respect consent when required.

## Goal

One product event (e.g. `signed_up` or `checkout_completed`) reaches an analytics sink; page views optional.

## Defaults (if unset)

- Privacy-friendly first-party or vendor the user already uses (PostHog, Plausible, GA4, etc.).
- Prefer server-side events for funnel-critical actions when easy.

## Minimum slice

1. Env names for write key / project id.
2. Provider initialized once (layout or analytics module).
3. One named event fired from a real user action.
4. Document how to see events in the vendor UI.

Out of scope for v1: full funnel dashboards, session replay — unless asked.

## Security / privacy

- Do not send passwords, tokens, or raw card data as event properties.
- Identify users only with stable opaque ids when possible.
- Honor cookie/consent banners when the app is public-facing in regulated regions (link legal templates if needed).

## Verify

- Trigger the action; event visible in vendor (or debug mode)
- No secrets in event payloads

## MCP

Usually none.
