# Cursor project starter

A blank repository that tells a Cursor agent how to stand up a new project: **MCP servers**, **skills**, **assets**, and **working memory** that survives across chats — including the loop from vague idea to live URL.

Cursor agents do not remember yesterday's thread. This repo treats **project rules** as memory, **skills** as runbooks, and **`assets/`** as the catalog the agent copies from.

## Use it

GitHub: https://github.com/icors2/Cursor_Forge

```bash
git clone https://github.com/icors2/Cursor_Forge.git
```

In Cursor on Windows: **File → Clone Repository** and paste that URL.

1. Clone this repo (or use it as a GitHub template).
2. Open the folder in Cursor.
3. In Agent chat, say what you are building. Example:

   > Bootstrap this repo for a Next.js dashboard. We'll use GitHub, Linear, and Vercel. Keep working memory updated.

4. The agent should follow `bootstrap-project` (and `scope-feature` for vague asks) before it writes product code.

If you only want the Cursor layout and no app yet, say so. The starter is valid on its own.

## What the agent is instructed to do

| Step | Where |
| --- | --- |
| Read the current snapshot | `.cursor/rules/memory.mdc` |
| First-run setup | `.cursor/skills/bootstrap-project/SKILL.md` |
| Scope a vague ask | `.cursor/skills/scope-feature` |
| Add tools | `.cursor/skills/add-mcp-server` + `assets/mcp-catalog.md` |
| Add auth/DB/payments/AI/… | `.cursor/skills/add-integration` + `assets/recipes/` |
| Prove a change works | `.cursor/skills/verify-change` |
| Polish UI | `.cursor/skills/polish-ui` |
| Security review | `.cursor/skills/security-review` |
| Deploy live URL | `.cursor/skills/deploy-app` |
| Ship / PR | `.cursor/skills/ship-change` |
| Debug / rollback | `.cursor/skills/debug-issue`, `checkpoint-rollback` |
| Check the layout + secrets | `npm run verify` |

## Layout

```text
AGENTS.md                      Always-on agent brief
.cursor/rules/                 Working memory (must be .mdc)
  00-core.mdc                  How this starter works
  10-memory-protocol.mdc       When to read/write memory
  20-security.mdc              Security non-negotiables
  30-frontend.mdc              Globbed UI habits
  memory.mdc                   Living snapshot (always on)
  decisions.mdc                Architecture choices
  conventions.mdc              Habits
  lessons.mdc                  Failure modes
.cursor/skills/                Runbooks the agent loads on demand
.cursor/mcp.json               Project MCP (starts empty, no secrets)
.cursor/agents/                Subagents (setup-verifier, security-reviewer)
.cursor/environment.json       Cloud Agent install stub
assets/
  mcp-catalog.md
  checklists/
  reference/                   structure, API, UX, cost, threat model, …
  recipes/                     auth, database, payments, AI, …
  stack-playbooks/             including opt-in golden-path.md
  templates/                   github, ci, config, docker, env, hooks, legal
scripts/
  audit-cursor-setup.mjs
  scan-secrets.mjs
.env.example                   Env var names only
```

## Working memory

Rules are injected into Agent context. That is the memory.

- **`memory.mdc`** — short snapshot: status, stack, focus, env **names**, enabled MCP.
- **`decisions.mdc`** — why you chose a stack or vendor.
- **`conventions.mdc`** — habits, not a style guide.
- **`lessons.mdc`** — mistake → signal → fix.
- **`20-security.mdc`** — always-on security constraints.

The agent is required to update these when it learns something that should still be true next week. Commit those edits.

Keep always-apply rules short. Long procedures belong in skills.

## MCP

`.cursor/mcp.json` starts as `{ "mcpServers": {} }`. The agent merges servers from `assets/mcp-catalog.md` using `${env:NAME}` for secrets.

You still need to:

1. Put values in a local `.env` (stdio) and/or **Cursor Cloud Secrets**.
2. Reload MCP in Cursor Settings.
3. For Cloud Agents, add HTTP MCP in the dashboard. Laptop `~/.cursor/mcp.json` does not apply there.

On Windows, bare `"command": "npx"` often fails — see the platform note in `assets/mcp-catalog.md`.

Never commit tokens.

## Local check

```bash
npm run verify
```

Runs the Cursor layout audit and a secret scan. Needs Node 18+. No install step. A warning that status is `unbootstrapped` is expected until the first real project is set up.

## After bootstrap

The agent should rewrite the **Project-specific** section of `AGENTS.md` with install, run, test, and verify steps for *your* app. This README stays about the starter; product docs go in `AGENTS.md` and, if useful, a new section you add here.

Copy boilerplate from `assets/templates/` only as needed (GitHub templates, CI, Docker, legal, hooks). Hooks stay **off** until you deliberately install them.

## Cloud Agents

User-level `~/.cursor/skills`, hooks, and MCP are invisible in the cloud. Keep what the project needs in this repo. `environment.json` `install` must stay idempotent; put long-running processes in `start` / `terminals` after you have an app.
