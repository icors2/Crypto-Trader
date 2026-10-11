# Recipe: AI feature

**Sensitive:** yes — always. Never put provider **secret** keys (including test-mode) in the client.

## Goal

One user-visible AI path (chat, summarize, generate) that runs through a **server** route or gateway, with a spend/latency bound.

## Defaults (if unset)

- Prefer a host gateway when available (e.g. Vercel AI Gateway, Netlify AI Gateway) so provider keys stay in the platform.
- Otherwise: official SDK on the server (OpenAI / Anthropic / Google) behind your API route.
- See `assets/reference/cost-and-quotas.md`.

## Minimum slice

1. Env names for the gateway or server key — never `NEXT_PUBLIC_*` / `VITE_*` for secret keys.
2. One API route or server action that calls the model.
3. Basic input limits (max chars / max tokens) and error surfacing.
4. UI that calls **your** backend, not the provider directly with a secret.

Out of scope for v1: multi-agent orchestration, fine-tuning, RAG over private docs — unless asked.

## Security

- Proxy all secret-key calls server-side (also in `.cursor/rules/20-security.mdc`).
- Do not put raw user secrets into prompts/logs.
- Validate/authorize who can invoke the expensive endpoint; rate-limit.
- Treat model output as untrusted if rendered as HTML.

## Verify

- Happy path returns a completion
- Missing/invalid auth on the route fails closed
- `security-review` on the AI route
- Confirm no provider secret in client bundle

## MCP

Optional docs MCP (`context7`). Provider MCPs only if needed.
