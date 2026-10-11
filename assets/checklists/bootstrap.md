# Bootstrap checklist

Use with the `bootstrap-project` skill.

## Product

- [ ] Purpose and name written in `.cursor/rules/memory.mdc`
- [ ] Stack chosen (or explicitly "template only"; golden-path only if no preference and confirmed)
- [ ] Deploy target recorded (or local-only)
- [ ] Threat model noted when auth/PII/payments/public API apply (`assets/reference/threat-model.md`)

## Cursor setup

- [ ] Status set to `bootstrapping`, then `active`
- [ ] MCP servers merged into `.cursor/mcp.json` from `mcp-catalog.md`
- [ ] Env **names** in `.env.example` and `memory.mdc` (no values)
- [ ] User told where to put secret values
- [ ] Domain skills added for repeatable workflows
- [ ] Needed templates copied from `assets/templates/` (CI, GitHub, config, docker, env)
- [ ] `AGENTS.md` Project-specific section rewritten
- [ ] Decision logged if a stack or vendor was chosen
- [ ] `npm run verify` is clean

## Do not

- [ ] No secrets in git
- [ ] No unused MCP servers
- [ ] No always-apply dump of this checklist
- [ ] No hooks installed unless the user asked
