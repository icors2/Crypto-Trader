---
name: scope-feature
description: Turn a vague product ask into one shippable slice. Use when the user says build me X, add a big feature, or the request spans many screens without a clear demo moment.
---

# Scope a feature

Anti-pattern: scaffolding five screens when one path proves the idea.

## When to use

- Vague asks ("build me an Airbnb", "add a dashboard")
- Feature requests that span auth + UI + API + deploy in one breath
- Before writing product code when the success criteria are unclear

## Steps

1. **Restate the goal** in one sentence the user would recognize.
2. **Name the demo moment** — the single thing they can click or run that proves it works.
3. **List out of scope** — at least three concrete cuts (e.g. no teams, no billing, no admin).
4. **Pick the thinnest end-to-end path** — one happy path from entry to that demo moment. Prefer existing stack and recipes in `assets/recipes/`.
5. **Confirm with the user** before building. Show: goal, demo moment, in-scope slice, out-of-scope list.
6. **Only then** implement. If they expand scope mid-flight, re-run this skill.

## Output shape

```text
Goal: …
Demo moment: …
In scope: …
Out of scope: …
Stack / recipes: …
```

## Verify

- User agreed (or explicitly waived confirmation)
- One demo moment, not a roadmap
- No second component library, auth provider, or database invented without need

## Failure modes

- Building the full vision "while we're here" → cut back to the demo moment
- Skipping confirmation on ambiguous asks → stop and confirm
