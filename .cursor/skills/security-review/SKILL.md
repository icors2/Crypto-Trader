---
name: security-review
description: Review a diff or feature for security issues. Use before shipping auth, payments, data access, public APIs, or any change that handles secrets or user input. Also use when the user asks for a security review.
---

# Security review

Repo-local review. Cloud Agents cannot see user-level `~/.cursor` security skills.

## When to use

- Before claiming a change that touches auth, payments, secrets, PII, or public endpoints is done
- After adding a database, file upload, webhook, or third-party integration
- When the user asks for a security review
- As a gate inside `ship-change`

## Preconditions

- Know the scope: a branch diff, a PR, or named files
- Read `assets/checklists/security-review.md`
- Prefer the `security-reviewer` subagent for a readonly pass; do the review yourself if you cannot launch one

## Steps

1. **Scope.** List the files and surfaces that changed (routes, queries, env, auth, uploads, webhooks).
2. **Threats.** For each surface, ask: who can call this, what data moves, what happens if input is hostile.
3. **Checklist.** Walk `assets/checklists/security-review.md`. Skip sections that clearly do not apply; do not skip auth or secrets when those files changed.
4. **Triage.** Label each finding: Critical / High / Medium / Low / Note.
5. **Report.** Return a short list. Each finding needs: severity, file path, what is wrong, and a concrete fix direction.
6. **Do not auto-fix** auth, crypto, access-control, or session logic. Flag those and wait for the user. Safe autofixes only: missing validation schemas, obvious injection via string-concat SQL, secrets accidentally written into a file you are already editing.

## Severity guide

| Severity | Examples |
| --- | --- |
| Critical | Auth bypass, secret in git, RCE, unrestricted SSRF |
| High | IDOR, SQLi/XSS with a realistic path, missing auth on a write |
| Medium | Missing rate limit, verbose errors leaking internals, weak CORS |
| Low | Missing security headers, overly broad scopes |
| Note | Defense-in-depth suggestions |

## Verify

- Findings quote real paths
- No invented CVEs
- Critical and High items are either fixed (safe ones) or explicitly left for the user

## Failure modes

- Rubber-stamping "looks fine" without reading the diff → re-run against the checklist
- Rewriting crypto/auth without a request → stop and ask
- Scanning the whole repo when the user asked about one PR → re-scope to the diff
