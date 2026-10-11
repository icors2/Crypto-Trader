# Playbook: Python HTTP API

Use when they asked for an API only and implied Python, or when there is no UI in sight.

## Scaffold

Prefer `uv`:

```bash
uv init
uv add fastapi uvicorn
```

Or FastAPI in a `src/` package with a `README` that shows `uv run uvicorn`.

## Structure

- Routers thin; services hold logic; Pydantic models at the boundary
- Align responses with `assets/reference/api-contracts.md`

## Verify

```bash
uv run ruff check .
uv run pytest
uv run uvicorn main:app --host 127.0.0.1 --port 8000
curl -sS http://127.0.0.1:8000/health
```

## Security

- Bind to `0.0.0.0:$PORT` in production
- Validate with Pydantic; parameterize DB access
- Threat model: `assets/reference/threat-model.md`
- MCP: `context7`; add `neon` / `supabase` only if you introduce Postgres

## After scaffold

- Do not add a database unless they need one.
- Write run/test steps into `AGENTS.md`. CI: `assets/templates/ci/python.yml`.
