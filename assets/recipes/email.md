# Recipe: Email

**Sensitive:** medium — no PII in logs; SPF/DKIM via provider.

## Goal

App sends one transactional email (e.g. welcome or magic link) reliably in a non-prod environment.

## Defaults (if unset)

- Resend, Postmark, SendGrid, or AWS SES — pick one. Avoid rolling SMTP unless required.

## Minimum slice

1. Env names: API key + `EMAIL_FROM`.
2. Server-side send helper (never call the email API from the browser with the secret).
3. One template or plain-text body used by a real flow.
4. Document how to view test sends (provider dashboard / Ethereal / etc.).

Out of scope for v1: marketing campaigns, complex template builders, unsubscribe center — unless asked.

## Security

- Secret API keys server-only.
- Do not log full email bodies if they contain tokens or PII.
- Rate-limit send endpoints that take a user-supplied address.

## Verify

- Trigger the flow; message appears in provider logs or inbox
- From-address matches verified domain (or provider test mode)

## MCP

Usually none. Use provider dashboard + `context7` for SDK docs.
