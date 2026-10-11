# Stack playbooks

Pick one during `bootstrap-project` only if the user wants a product scaffolded now.

| File | When |
| --- | --- |
| `golden-path.md` | **Opt-in** — user stated **no** stack preference (Next + Tailwind + shadcn + Postgres + Vercel) |
| `web-nextjs.md` | They asked for Next.js / App Router specifically |
| `web-vite.md` | They asked for Vite, or a static/toy/game UI |
| `api-python.md` | HTTP API, Python implied or no UI |
| `api-node.md` | HTTP API in Node/TypeScript |
| `worker-queue.md` | Background jobs / queues |
| `cli.md` | Command-line tool or script |

Do not invent a monorepo. Do not add auth or a database unless the request needs it.

`golden-path.md` is **not** mandatory — if they named any stack, honor it.

Also read: `assets/reference/project-structure.md`, `api-contracts.md`, `observability.md`, `threat-model.md`, `cost-and-quotas.md`, `ui-design.md`.
