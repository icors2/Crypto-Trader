# Optional Cursor hooks (not active by default)

These scripts are **templates**. Copy them into `.cursor/hooks/` and add `.cursor/hooks.json` only when you intentionally want every Agent run gated.

## Why they are inert

Hooks silently affect every agent turn (and Cloud Agents pick up project `.cursor/hooks.json`). A bad deny rule blocks legitimate work. Enable only after you understand the matchers.

## Install

1. Copy `hooks.json` → `.cursor/hooks.json`
2. Copy `*.mjs` → `.cursor/hooks/`
3. Reload Cursor / start a new Agent chat
4. Confirm a safe command still works; then try a blocked pattern

## Scripts

| Script | Hook | Behavior |
| --- | --- | --- |
| `guard-shell.mjs` | `beforeShellExecution` | Denies destructive git (`reset --hard`, `clean -fd`, force push / `+ref`), reckless deletes, and shell dumps of `.env`/keys |
| `redact-read.mjs` | `beforeReadFile` | Denies reading `.env`, private keys, credential JSON (checks `file_path`) |
| `verify-on-stop.mjs` | `stop` | Reminds the agent to run verification (does not block) |

Deny hooks use `"failClosed": true` so crash/timeout/invalid JSON blocks the action. Scripts are **Node `.mjs`**, not `.sh` — portable to Windows and Linux Cloud Agents.

## Limits (known)

- Prefer `.cursorignore` / `.gitignore` for `.env` even when hooks are enabled — hooks are defense-in-depth, not a boundary.
- `failClosed: true` on deny hooks trades availability for safety (crash = block).
- Shell deny patterns are heuristics; clever wrappers can bypass them.
- Local `scan-secrets` covers `git ls-files` only; enable Gitleaks in CI for history.

## Shape

Project hooks run from the **repo root**. Exit code `2` blocks. JSON on stdout:

```json
{
  "continue": true,
  "permission": "deny",
  "user_message": "…",
  "agent_message": "…"
}
```

See Cursor hooks docs for matchers, timeouts, and Cloud support.
