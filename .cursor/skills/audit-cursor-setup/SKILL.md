---
name: audit-cursor-setup
description: Validate Cursor rules, skills, MCP config, and working memory. Use after bootstrap, after adding MCP or skills, or when setup looks broken.
---

# Audit Cursor setup

## Run the checker

```bash
npm run verify
```

This runs `scripts/audit-cursor-setup.mjs` then `scripts/scan-secrets.mjs`.

Fix every error it reports. Treat warnings as real unless you have a reason to keep them. An `unbootstrapped` warning is expected for the blank starter.

## Manual checks the script cannot do

1. `.cursor/rules/memory.mdc` matches reality (stack, MCP list, status).
2. `AGENTS.md` **Project-specific** is not still the placeholder if Status is `active`.
3. `.cursor/mcp.json` has only servers this project uses, each with `${env:…}` for secrets.
4. The user has set those env vars / Cloud Secrets. You cannot see the values — ask.
5. No secrets in git (`git grep` for `sk-`, `ghp_`, `xoxb-`, `AKIA` if relevant).
6. Cloud: `environment.json` `install` is idempotent; no long-running servers in `install`.

## If MCP is missing in Cloud Agents

Repo `mcp.json` is not enough. The user still needs dashboard / team MCP. Say so. Do not pretend laptop `~/.cursor/mcp.json` will apply.
