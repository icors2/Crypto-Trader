# Playbook: CLI or script

Use when the deliverable is a command, not a website.

## Scaffold

- Language they named; Python + `uv` if they named none.
- `uv init` or the language's official init.
- Entry point documented in `README.md` and `AGENTS.md`.

## Structure

- One clear entry (`__main__`, `bin/`, or `src/cli.ts`)
- Parse args with a real parser; validate paths and URLs
- See `assets/reference/project-structure.md`

## Verify

```bash
# Replace with the real entry
uv run python -m your_pkg --help
# or: node dist/cli.js --help
# Run a golden-path command against a fixture
```

## Security

- Do not log secrets passed via flags or env
- Treat file paths and URLs from users as untrusted
- No unused MCP; `context7` if library docs matter

## After scaffold

- No web preview.
- Add a skill only if the CLI has a multi-step release or data workflow.
