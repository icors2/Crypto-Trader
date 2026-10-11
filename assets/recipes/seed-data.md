# Recipe: Seed data

**Sensitive:** no (keep seeds free of real PII and secrets).

## Goal

Fresh install shows a believable UI — lists, cards, and empty states are intentional, not broken-looking blank pages.

## Defaults (if unset)

- A `db:seed` (or `prisma db seed` / Django loaddata) script documented in `AGENTS.md`.
- Factories over huge static JSON when possible.

## Minimum slice

1. Seed script creates enough rows for the main list/detail views.
2. Idempotent or clearly "wipe and reseed" local-only.
3. One demo user if auth exists (documented password only in local docs / `.env.example` placeholders — never real prod creds).
4. Empty-state path still works when seed is skipped.

Out of scope: production data migrations disguised as seeds.

## Security

- No real customer data in seeds committed to git.
- No live API keys in seed files.

## Verify

- `npm run db:seed` (or equivalent) then open the main UI
- App usable without seed (empty states)

## MCP

None required.
