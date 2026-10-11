# Lightweight threat model

Run during `bootstrap-project` (or when adding a major surface). Write short answers into `decisions.mdc` or keep them in the PR that introduces the surface. Six questions is enough.

## 1. What data do we handle?

List data classes: public, account, PII, payment, secrets, health, etc. Note retention if known.

## 2. What are the trust boundaries?

Examples: browser → API, API → database, webhook → app, agent → MCP, CI → deploy. Name the crossing points where validation or auth must happen.

## 3. Who is the attacker?

Pick the realistic ones: anonymous internet user, authenticated user attacking another tenant, stolen session, malicious dependency, insider with repo access. Do not invent nation-state threats for a toy app.

## 4. What is the blast radius?

If one secret, one account, or one server is compromised, what else falls? Prefer isolation (separate keys, least privilege, no shared admin).

## 5. What is logged?

What events matter for security (auth failures, privilege changes, payments)? Confirm logs never contain secrets or raw PII.

## 6. What is the recovery path?

How do you rotate keys, revoke sessions, and restore data? If the answer is "we don't know," write that down as an open risk.

## Output shape

```text
Data: …
Boundaries: …
Attackers: …
Blast radius: …
Logging: …
Recovery: …
Open risks: …
```
