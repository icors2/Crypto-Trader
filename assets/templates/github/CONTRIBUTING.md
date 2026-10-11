# Contributing

## Setup

1. Clone the repo and open it in Cursor (or your editor).
2. Copy `.env.example` to `.env` and fill values locally — never commit `.env`.
3. Follow install / run / test in `AGENTS.md` (Project-specific).

## Workflow

1. Create a branch from `main`.
2. Make a focused change.
3. Run verification (`verify-change` / project test scripts). For security-sensitive work, run a security review.
4. Open a PR using the PR template. Conventional commits preferred (`feat:`, `fix:`, …).

## Agent / Cursor notes

- Working memory lives in `.cursor/rules/`. Update it when you learn durable facts.
- Do not enable unused MCP servers. Do not paste secrets into `mcp.json`.

## Code review

- Prefer small PRs.
- Explain why in the PR body; tests and screenshots beat long prose.
