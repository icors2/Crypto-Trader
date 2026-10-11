# Playbook: Golden path (opt-in)

**Use only when the user has no stack preference.** This is one labeled option, not a mandatory default. If they named a stack, use that playbook instead (`web-nextjs`, `web-vite`, `api-node`, `api-python`, `cli`, `worker-queue`).

## Stack

| Layer | Choice |
| --- | --- |
| App | Next.js App Router + TypeScript |
| UI | Tailwind CSS + shadcn/ui (one kit only) |
| Data | Postgres (Neon or Supabase) |
| Host | Vercel |
| Tests | Vitest |
| Browser verify | Playwright MCP or Chrome DevTools MCP |

## Scaffold

Follow `web-nextjs.md` for `create-next-app`, then:

1. Add shadcn/ui if UI is needed.
2. Add Postgres only when the request needs durable data (`assets/recipes/database.md` via `add-integration`).
3. Enable MCP: `context7`; `vercel` when deploying; DB vendor MCP only if used; browser MCP for UI verify.
4. Copy useful templates from `assets/templates/` (CI node, env, GitHub) as needed.
5. Threat model if auth/PII/payments appear.

## Verify

```bash
npm run lint
npm run build
# smoke the demo moment in the browser
```

Before a public URL: `polish-ui`, then `deploy-app`.

## Security

- No provider secrets in the client (`20-security.mdc`)
- Recipes for auth/payments/AI as needed
- `assets/reference/cost-and-quotas.md` when enabling AI

## After scaffold

Write install/run/test/deploy into `AGENTS.md`. Record this golden-path choice in `decisions.mdc`.
