---
name: deploy-app
description: Deploy the app to a live URL (preview then production). Use when the user asks to deploy, ship live, get a URL, or promote a preview. Vendor-agnostic; reads deploy target from memory.mdc.
---

# Deploy the app

Get a real URL. Local `.env` is not production secrets.

## When to use

- User asks to deploy, go live, or get a preview/production URL
- After a feature is verified and ready to show

## Preconditions

1. `verify-change` passed (or user explicitly waived).
2. Deploy target recorded in `.cursor/rules/memory.mdc` (or ask once).
3. Platform secrets set in the host (Vercel/Render/Cloudflare/etc.) — **not** only in local `.env`.
4. Security-sensitive surfaces already reviewed when applicable.

## Steps

1. **Read target** from `memory.mdc` → Deploy target. If unset, ask: Vercel, Render, Cloudflare, Netlify, other, or local-only.
2. **Build** with the project's production build command from `AGENTS.md`.
3. **Preview deploy** first when the platform supports it.
4. **Smoke-check the live URL** — hit the demo moment / health endpoint. Browser or curl. Do not claim deployed if the URL errors.
5. **Promote** to production only if preview looks good (or user asked for prod directly).
6. **Record** in `AGENTS.md` Project-specific: public URL, how to redeploy, how to roll back.
7. **MCP** — use the matching server from `assets/mcp-catalog.md` when available:

| Target | Catalog entry |
| --- | --- |
| Vercel | `vercel` |
| Render | `render` |
| Cloudflare | `cloudflare` |

User-level plugin deploy skills (Netlify, Render, …) may exist on the laptop but **do not reach Cloud Agents**. Prefer this skill + catalog MCP.

## Verify

- URL returned and smoke-checked
- Secrets not printed in chat or logs
- Rollback path known (previous deploy / git revert + redeploy)

## Failure modes

- Deploying with secrets only in local `.env` → set platform env first
- Skipping smoke check → open the URL before declaring success
- Treating "build succeeded" as "site works" → check the real URL
