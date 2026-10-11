---
name: checkpoint-rollback
description: Create a git checkpoint before risky work, or roll back when something breaks. Use before migrations, large refactors, experiments, or when the user panics after a bad change.
---

# Checkpoint and rollback

Git saves code. **Migrations and uploaded files are not covered by git** — that is where vibe coders lose data.

## When to use

- Before a risky change (schema migration, auth rewrite, dependency major bump)
- When the user says undo, roll back, or "go back to when it worked"
- Before an experiment the user might abandon

## Checkpoint (before risk)

1. Ensure the working tree is intentional (`git status`).
2. Commit a checkpoint with a clear message, e.g. `chore: checkpoint before auth migration`.
3. Optionally create a branch: `git branch checkpoint/YYYYMMDD-topic`.
4. Tell the user the commit hash / branch name.

## Rollback (after breakage)

Pick the lightest option that fits:

| Situation | Action |
| --- | --- |
| Uncommitted local edits | `git restore -- <paths>` or `git checkout --` |
| Bad commit, not pushed / ok to rewrite with user OK | `git revert <sha>` (prefer) or reset only if user explicitly wants it on a private branch |
| Need the old tree but keep history | `git revert` or recreate files from `git show checkpoint-sha:path` |
| Deployed bad build | Redeploy previous release via `deploy-app` / platform rollback — not only git |

**Never** `git reset --hard` or force-push shared `main` unless the user explicitly demands it and understands the cost.

## Data outside git

Before rolling back code that assumed a new schema or blob layout:

1. Confirm whether a migration already ran in shared/prod databases.
2. Prefer a forward fix or a down-migration (`migrate-database`) over pretending git restore undoes the database.
3. Uploaded files in object storage stay until deleted — plan restore or accept loss.

## Verify

- Checkpoint hash shared with the user when creating one
- After rollback: app boots; critical path smoke-checked
- Database/blob state explicitly called out if relevant

## Failure modes

- Assuming `git restore` undoes a production migration → stop and use `migrate-database`
- Force-pushing main to "fix" history → use `revert` instead
- Rolling back without telling the user what is still changed in the DB → say it plainly
