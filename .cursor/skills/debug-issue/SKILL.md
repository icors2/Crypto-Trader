---
name: debug-issue
description: Systematic debug loop for paste-an-error or broken behavior. Use when something fails, the user pastes a stack trace, or a verify/deploy step breaks.
---

# Debug an issue

Anti-pattern: changing five files at once and hoping.

## When to use

- User pastes an error or says "it's broken"
- Tests, build, deploy, or runtime fail after a change
- Intermittent or "works on my machine" reports

## Steps

1. **Capture the exact error** — full message, stack, command, URL, repro steps. Do not paraphrase away details.
2. **Reproduce** — run the failing path yourself. If you cannot reproduce, say so and gather more signal.
3. **Isolate** — one failing surface (file, query, request). Prefer reading logs and the smallest repro over rewriting.
4. **One hypothesis** — state it in one sentence. Only then change code aimed at that hypothesis.
5. **Minimal fix** — smallest diff that addresses the cause. No drive-by refactors.
6. **Regression check** — re-run the failing command/path; add a smoke or unit check when the bug was non-obvious.
7. **Lesson** — if the failure will recur for later agents, add an entry to `.cursor/rules/lessons.mdc` via `update-working-memory`.

## Verify

- Original failure no longer reproduces
- You stated the hypothesis and the fix
- No unrelated files changed "while debugging"

## Failure modes

- Shotgun edits across the codebase → revert extras; one hypothesis at a time
- Fixing symptoms (catch-all try/except) without finding the cause → dig one layer deeper
- Claiming fixed without re-running the failing path → reproduce green
