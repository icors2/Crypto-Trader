# Agent instructions

This repo is a **Cursor project starter**. It is blank on purpose. Your job on first use is to turn it into a working project: MCP servers, skills, assets, and durable working memory.

Read `.cursor/rules/memory.mdc` before you write application code.

## Bootstrap (new project from this template)

If working memory `Status` is `unbootstrapped` or `bootstrapping`:

1. Follow the `bootstrap-project` skill (`.cursor/skills/bootstrap-project/SKILL.md`).
2. Infer the product and stack from the user's request. Ask only for decisions you cannot infer. Vague asks → `scope-feature` first.
3. Enable **only** the MCP servers this project will use. Copy configs from `assets/mcp-catalog.md` into `.cursor/mcp.json`. Use `${env:NAME}` — never real secrets.
4. Add project skills for multi-step workflows. Use `create-project-skill`.
5. Copy or create assets the project actually needs from `assets/` (templates, checklists, playbooks, recipes).
6. Run a lightweight threat model (`assets/reference/threat-model.md`) when the product handles auth, PII, payments, or public APIs.
7. Persist what you learned with `update-working-memory`.
8. Rewrite the **Project-specific** section below so later agents know how to run, test, and verify.
9. Finish with `npm run verify` (audit + secret scan).

Do not scaffold a platform the user did not ask for. Ship one complete, usable slice.

## Vibe loop (build → live URL)

1. Vague ask → `scope-feature` (one demo moment).
2. Build the slice; use `add-integration` + `assets/recipes/` for auth/DB/payments/AI/etc.
3. Breaks → `debug-issue`. Panic → `checkpoint-rollback` (git does not undo DB/uploads).
4. `verify-change` (smoke the critical path — compile alone is not enough).
5. User-facing UI → `polish-ui` before a public URL.
6. Security-sensitive → `security-review`.
7. Live URL → `deploy-app`. PR → `ship-change`.
8. Gate on `assets/checklists/definition-of-done.md`.

## Where knowledge lives

| Kind | Put it here | Apply |
| --- | --- | --- |
| Durable facts, decisions, conventions, lessons | `.cursor/rules/*.mdc` | Working memory. Commit it. |
| Security non-negotiables | `.cursor/rules/20-security.mdc` | Always |
| Multi-step workflows | `.cursor/skills/<name>/SKILL.md` | On demand / by relevance |
| Feature recipes (auth, payments, …) | `assets/recipes/` | Via `add-integration` |
| Shared tools | `.cursor/mcp.json` | Project MCP (no secrets) |
| Catalogs, templates, playbooks, checklists | `assets/` | Read when needed |
| How to run and test | this file | Always |

Rules are short constraints. Skills are procedures. Do not dump a playbook into an always-apply rule.

## Working memory

Cursor does not keep chat history as memory. **Rules are the memory.**

- At the start of non-trivial work, read `.cursor/rules/memory.mdc`.
- After you learn a durable fact, decision, convention, or failure mode, follow `update-working-memory`.
- Keep `memory.mdc` short. Move detail into `decisions.mdc`, `conventions.mdc`, or `lessons.mdc`.
- Commit memory updates so later sessions and Cloud Agents inherit them.

## Hard constraints

- Never commit secrets. Never write tokens into rules, skills, `mcp.json`, or `assets/`.
- Never call AI/payment providers from the client with a secret key (including test-mode secrets).
- Project rules **must** be `.mdc`. A `.md` file in `.cursor/rules/` is ignored.
- Skill `name` in frontmatter **must** match the parent folder.
- User-level `~/.cursor/*` is **not** available to Cloud Agents. Keep everything this project needs in the repo.
- Sandbox may block writes to `.cursor/*.json`. If you cannot edit `mcp.json`, tell the user what to paste.
- Do not enable Cursor hooks from `assets/templates/hooks/` unless the user asked — they change every agent run.
- Cost awareness: `assets/reference/cost-and-quotas.md`.

## Cursor Cloud specific instructions

- User MCP, user skills, and user hooks do not apply here. Use repo files only.
- `.cursor/environment.json` `install` must stay idempotent. Long-running processes belong in `start` / `terminals`.
- Cloud MCP is configured in the Cursor dashboard as well as (optionally) `.cursor/mcp.json`. Prefer HTTP MCP. SSE and `mcp-remote` are not supported in Cloud Agents.
- After bootstrap, put Cloud-only setup notes in this section.

## Project-specific

_Status: not bootstrapped._

Replace this section during bootstrap with:

- What this product is
- Stack and package manager
- How to install, run, test, and lint
- Required environment variables (names only)
- Enabled MCP servers and why
- How to verify a change (browser, tests, or CLI)
- Deploy URL and rollback (after first deploy)
