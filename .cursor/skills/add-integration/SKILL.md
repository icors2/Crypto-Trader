---
name: add-integration
description: Add a product integration (auth, database, payments, email, AI, uploads, realtime, analytics, seed data) using assets/recipes/. Use when the user asks for login, Stripe, Postgres, file upload, email, chatbots, or similar.
---

# Add an integration

One procedure; stack-specific detail lives in `assets/recipes/`.

## When to use

- User asks for auth, DB, payments, uploads, email, AI features, realtime, analytics, or seed data
- Bootstrap uncovered a needed external system

## Steps

1. **Pick the recipe** from `assets/recipes/README.md` that matches the ask.
2. **Pick a vendor** — use what `memory.mdc` already records; otherwise prefer the recipe's default and confirm if non-obvious.
3. **Read the recipe** end-to-end before coding.
4. **MCP** — enable a catalog server via `add-mcp-server` only if the agent will call that vendor's tools this session.
5. **Env names** — add to `.env.example` and `memory.mdc` (names only). Tell the user where to put values.
6. **Thinnest working slice** — follow the recipe's "minimum slice." Do not build admin UIs or optional extras on day one. **Do not skip** security-required pieces called out in the recipe (e.g. Stripe signature-verified webhooks, auth on protected routes).
7. **Verify** — `verify-change` for the new path. Run `security-review` when the recipe is marked sensitive (auth, payments, uploads, AI with user data, email with tokens, database with PII/multi-tenant).
8. **Decide** — log vendor choice in `decisions.mdc` if it was non-obvious.

## Recipes index

See `assets/recipes/README.md`.

Local vendor skills (Supabase, Stripe, Vercel, …) may exist under `~/.cursor` but **do not reach Cloud Agents**. The repo recipe is the portable copy.

## Verify

- Demo path from the recipe works
- No secrets in git
- Memory / `.env.example` updated

## Failure modes

- Enabling the whole MCP catalog "just in case" → only what you will call
- Implementing every recipe option at once → one slice
- Skipping security-review on auth/payments/uploads → run it
