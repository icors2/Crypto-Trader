---
name: update-working-memory
description: Persist durable project knowledge into Cursor rules. Use at the end of bootstrap, after a decision, after a repeated mistake, or whenever a fact should survive into the next chat.
---

# Update working memory

## Where to write

| Content | File | Apply mode |
| --- | --- | --- |
| Snapshot: status, stack, focus, env names, MCP, skills | `.cursor/rules/memory.mdc` | Always |
| Architecture / tool choice and why | `.cursor/rules/decisions.mdc` | Intelligent |
| Habit the codebase should keep | `.cursor/rules/conventions.mdc` | Intelligent |
| Mistake, signal, fix | `.cursor/rules/lessons.mdc` | Intelligent |
| Multi-step how-to | new/updated skill | On demand |

If a fact belongs in two places, keep the canonical copy in one file and point to it.

## How to edit `memory.mdc`

1. Keep the existing headings.
2. Replace stale bullets. Do not append contradictory ones.
3. Set **Updated** to today's date.
4. Keep the file short (~80 lines). Move narrative to decisions/lessons.
5. Names of secrets only. Never values.
6. Leave `alwaysApply: true` in the frontmatter.

## How to edit the other memory rules

- Newest entries first.
- Use the comment templates already in those files.
- One idea per entry. Concrete, not vague.
- If a rule grows past a few hundred lines, split it.

## New domain rules

When a convention only applies to some files, add a globbed rule:

```markdown
---
globs: src/**/*.tsx
alwaysApply: false
---

- …
```

Copy `assets/templates/rule.template.mdc`. Never use `.md` under `.cursor/rules/`.

## Finish

- If run/test steps changed, update the **Project-specific** section of `AGENTS.md`.
- Commit memory updates with the rest of the work so later agents inherit them.
