# Security review checklist

Use with the `security-review` skill or the `security-reviewer` subagent. Skip sections that clearly do not apply.

## Secrets and keys

- [ ] No secrets in git, rules, skills, `mcp.json`, or templates
- [ ] `.env.example` has names only (no assigned values)
- [ ] Keys are rotatable; docs say where to put them (local `.env` / Cloud Secrets)
- [ ] Service accounts and tokens use least privilege

## Input and injection

- [ ] Untrusted input validated at the boundary (schema / allowlist)
- [ ] SQL / NoSQL queries parameterized
- [ ] Shell and file paths do not interpolate raw user input
- [ ] HTML / templates escape or sanitize user content (XSS)
- [ ] Uploads: type, size, and storage path are constrained

## Authn and authz

- [ ] Authentication is required where intended
- [ ] Authorization checks the actor against the resource (no IDOR)
- [ ] Sessions / tokens have expiry and secure cookie flags when applicable
- [ ] Password reset / magic links are single-use and time-limited
- [ ] Multi-tenant data is scoped by tenant on every query

## Network and SSRF

- [ ] Server-side fetches do not take unrestricted user URLs
- [ ] Webhooks verify signatures / shared secrets
- [ ] CORS is explicit; not `*` with credentials
- [ ] TLS in production; no secrets over plain HTTP

## Errors, logs, and observability

- [ ] Error responses do not leak stack traces or internals to clients
- [ ] Logs omit passwords, tokens, session IDs, and raw PII
- [ ] Security-relevant events (login failure, authz deny) are logged

## Dependencies and supply chain

- [ ] New dependencies are needed and from trusted sources
- [ ] Lockfiles are committed
- [ ] Known critical CVEs are addressed or accepted with a reason

## Transport and headers (web)

- [ ] Security headers considered (CSP, HSTS, X-Content-Type-Options, frame options)
- [ ] Cookies: `Secure`, `HttpOnly`, `SameSite` as appropriate

## Recovery

- [ ] Compromised-key playbook exists (rotate, revoke sessions, notify)
- [ ] Backups / restore path known if data is durable
