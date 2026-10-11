# Cost and quotas

Surprise bills kill vibe projects. Cap spend before you scale prompts or leave always-on services running.

## What actually costs money

| Driver | Why it bites |
| --- | --- |
| AI tokens | Chat loops, large contexts, image gen, retries |
| Egress / bandwidth | Media, downloads, chatty APIs |
| Always-on compute | Free tiers that sleep still convert to paid; forgotten workers |
| Database rows / storage | Seeds gone wild; log tables; uploads |
| Third-party seats | Auth, email, analytics MAUs |

## Habits

- Prefer host **AI gateways** and platform env for keys (see `assets/recipes/ai-feature.md`).
- Set provider **usage limits** / billing alerts on day one.
- Cap max tokens and input length on every AI route.
- Do not leave `npm run dev` tunnels or paid GPU sandboxes running overnight without intent.
- Watch free-tier **expiry** (trial clocks on DB/hosting).

## Agent rules of thumb

- Before adding a second AI call in a hot path, ask whether one call + caching would do.
- Do not enable unused MCP servers that hammer paid APIs in loops.
- Document estimated cost drivers in `decisions.mdc` when choosing a paid vendor.

## Pointers

- Security of keys: `.cursor/rules/20-security.mdc`
- Deploy env: `deploy-app` skill
