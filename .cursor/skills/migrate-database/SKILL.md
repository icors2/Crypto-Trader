---
name: migrate-database
description: Write and apply database migrations safely. Use when changing schema, adding tables/columns, or the user asks to migrate. Additive-first; destructive changes need explicit confirmation.
---

# Migrate the database

Schema changes can destroy data. Git does not undo a production migration.

## When to use

- Adding or changing tables, columns, indexes, constraints
- User asks to migrate, sync schema, or "update the database"

## Preconditions

1. Know which database (local vs shared/prod) you are targeting.
2. Prefer a checkpoint (`checkpoint-rollback`) before risky migrations.
3. Tooling from the project's stack (Prisma, Drizzle, Django, Alembic, Supabase CLI, …).

## Steps

1. **Inspect** current schema / migration history. Do not invent a second migration system.
2. **Write** a new migration. Prefer **additive** changes (add column/table nullable or with default).
3. **Down / reverse** — include a reversible path when the tool supports it, or document manual reverse steps.
4. **Dry-run** when available (generate SQL and read it).
5. **Backup / restore path** — for shared or prod: confirm a backup or platform restore exists before apply. If none, stop and tell the user.
6. **Apply** to the intended environment only.
7. **Verify** — app boots; critical queries work; `verify-change` smoke path.
8. **Never edit** an migration that already applied in a shared environment. Write a new one instead.

## Destructive changes

Dropping columns/tables, tightening nullability, or rewriting data requires **explicit user confirmation** naming the environment and the data risk.

## Verify

- Migration applied (or deliberately not, with reason)
- App works against the new schema
- User knows which env was touched

## Failure modes

- Editing an already-applied migration file → new migration instead
- Running prod migrations because local failed → stop; fix local first
- Assuming git rollback restores the DB → it does not; see `checkpoint-rollback`
