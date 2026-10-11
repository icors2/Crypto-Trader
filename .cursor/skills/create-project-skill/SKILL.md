---
name: create-project-skill
description: Create a Cursor project skill with valid frontmatter and folder layout. Use when adding a repeatable workflow (deploy, migrate, review, design-to-code) or when the user asks for a new skill.
---

# Create a project skill

Skills are procedures. Rules are constraints. If it is a one-line convention, write a rule instead.

## Layout

```text
.cursor/skills/<name>/SKILL.md
```

Optional: `scripts/`, `references/`, `assets/` next to `SKILL.md`. Keep `SKILL.md` under ~500 lines; load references on demand.

`name` in frontmatter **must** match the folder. Lowercase, digits, hyphens. Max 64 characters.

## Frontmatter

```markdown
---
name: deploy-preview
description: What it does and when to use it. The agent matches on this text.
---
```

Optional fields:

| Field | Use |
| --- | --- |
| `paths` | Only surface when matching files are in play |
| `disable-model-invocation` | `true` = slash command only (`/deploy-preview`) |

Do not use legacy `globs` on new skills.

## Body

Write like an internal runbook:

1. When to use
2. Preconditions
3. Numbered steps
4. Verification
5. Failure modes

Reference files with paths. Do not paste large code samples.

## Steps for you

1. Choose a kebab-case name that is not already a folder under `.cursor/skills/`.
2. Copy `assets/templates/SKILL.template.md` and fill it in.
3. Add any scripts or references the skill needs.
4. List the new skill in `.cursor/rules/memory.mdc` → Environment.
5. If the workflow is also a user-facing slash command, set `disable-model-invocation: true`.
