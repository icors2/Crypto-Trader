# Recipe: Database

**Sensitive:** yes when multi-tenant or PII.

## Goal

App reads and writes durable data through a single data layer; schema is migrated, not hand-edited in prod.

## Defaults (if unset)

- Postgres via Neon or Supabase when on Vercel-like hosts.
- ORM: Prisma or Drizzle (TS); SQLAlchemy/Django (Python). Match the stack playbook.

## Minimum slice

1. Connection string env name in `.env.example` (e.g. `DATABASE_URL`).
2. One model/table used by a real feature path.
3. Migration workflow via `migrate-database` (not ad-hoc SQL in prod).
4. Local (or branch) DB documented in `AGENTS.md`.

Out of scope for v1: read replicas, sharding, full admin CRUD.

## Security

- Parameterized queries only.
- Tenant / user scoping on every query when multi-tenant.
- Least-privilege DB roles when the host supports them.
- Never commit connection strings.
- **Supabase / PostgREST:** enable **RLS** with deny-by-default policies before exposing tables to the anon/authenticated client. Do not ship open tables with a public anon key.

## Verify

- Migrate apply succeeds
- Feature path reads/writes
- Smoke check after migrate

## MCP

`neon` or `supabase` from the catalog when the agent will provision or inspect via MCP.
