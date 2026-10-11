---
name: ship-change
description: Branch, commit with conventional commits, open a PR, and wait on CI. Use when the user asks to ship, open a PR, or land a change. Requires verify-change and security-review first when applicable.
---

# Ship a change

## When to use

- User asks to commit, open a PR, or ship
- A feature/fix is verified and ready for review

## Preconditions

1. `verify-change` has passed for this work (or the user waived it explicitly).
2. If the diff touches auth, payments, secrets, PII, or public data access, `security-review` has run (or user waived).
3. Working tree is intentional — no leftover debug or secrets.

## Steps

1. **Status.** `git status`, `git diff`, and recent `git log` so the message matches the repo style.
2. **Branch.** Create or use a feature branch. Do not commit directly to `main`/`master` unless the user said to.
3. **Stage.** Add only related files. Never stage `.env` or credential files.
4. **Commit.** Conventional commits, imperative subject, no trailing period:

   ```text
   <type>[optional scope]: <description>
   ```

   Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `style`. Body explains why when useful.
5. **Push.** Upstream tracking as needed. Do not force-push shared branches unless asked.
6. **PR.** Open with `gh pr create` when GitHub is in use. Body: summary, test plan (commands from verify-change), security notes if any.
7. **CI.** Watch checks if they exist. Fix failures before declaring shipped.

## Verify

- Commit exists on the remote branch
- PR URL shared with the user when opened
- No secrets in the diff

## Failure modes

- Committing without verify → stop and run `verify-change`
- Rewriting auth/crypto in the same PR as a drive-by → split or flag via security-review
- `git commit --no-verify` to bypass hooks → do not, unless the user insists and understands the risk
- Pushing to main when the project uses PRs → use a branch + PR
