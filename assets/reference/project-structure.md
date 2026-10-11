# Project structure

Guidance for agents scaffolding or growing an app. Prefer official scaffolds; then align with one pattern below.

## Choose a layout

| Pattern | When |
| --- | --- |
| **Feature folders** (`src/features/billing/…`) | Product UI with many domains; colocate UI + hooks + tests |
| **Layered** (`src/routes`, `src/services`, `src/db`) | APIs and CLIs; clear dependency direction inward |
| **Framework default** | Next.js App Router, Vite `src/`, FastAPI package — stay close to the scaffold |

Do **not** invent a monorepo unless multiple deployables or shared packages are real requirements.

## Where things go

- **App entry** — framework default (`app/`, `src/main.tsx`, `main.py`)
- **Domain logic** — not inside route handlers if it will be reused or tested alone
- **Tests** — colocated `*.test.ts` / `test_*.py` or a top-level `tests/` mirroring `src/`
- **Fixtures** — `tests/fixtures/` or `__fixtures__/` next to tests; factories over brittle snapshots
- **Config** — env via process/platform env; validate at startup; names documented in `.env.example`
- **Scripts** — `scripts/` for repo tooling (audit, migrate), not business features
- **Cursor** — `.cursor/rules`, `.cursor/skills`, `.cursor/mcp.json` stay project-owned

## Dependency direction

```text
UI / HTTP handlers → application services → domain → adapters (DB, HTTP clients)
```

Adapters may depend on frameworks; domain should not.

## Monorepos

Justified when: separate apps with a shared package, or multiple deploy targets from one repo.

Avoid when: a single app would do. Extra packages slow agents and humans without payoff.

## After choosing

Record the layout in `decisions.mdc` and point `AGENTS.md` at install/run/test paths.
