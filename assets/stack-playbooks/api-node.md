# Playbook: Node HTTP API

Use when they want an API in Node/TypeScript without a heavy UI (or UI comes later).

## Scaffold

Prefer a small Fastify or Hono app under `src/`, TypeScript strict, official init when available:

```bash
npm init -y
npm pkg set type=module
npm i fastify
npm i -D typescript @types/node tsx vitest
npx tsc --init
```

Or Hono + a platform adapter if they named Cloudflare / edge deploy.

## Structure

- `src/routes` or feature modules → handlers
- `src/services` → business logic
- Validation at the boundary (Zod or equivalent)
- Follow `assets/reference/api-contracts.md` for envelope and errors

## Verify

```bash
npm run typecheck   # or npx tsc --noEmit
npm test
curl -sS http://127.0.0.1:$PORT/health
```

## Security

- Validate input; parameterize DB access
- No secrets in repo; bind `0.0.0.0:$PORT` in production
- Threat model: `assets/reference/threat-model.md`
- MCP: `context7`; add DB MCP only if you introduce Postgres

## After scaffold

Write install/run/test into `AGENTS.md`. Add CI from `assets/templates/ci/node.yml` if they use GitHub.
