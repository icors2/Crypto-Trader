# Cursor Cloud `environment.json` examples

Copy one of these into `.cursor/environment.json` during bootstrap (or merge fields).

| File | When |
| --- | --- |
| `environment.node.json` | Node / Next / Vite apps |
| `environment.python.json` | Python / FastAPI apps |

## Rules

- **`install`** must be idempotent (deps only). No long-running servers.
- Put long-running processes in **`start`** and/or **`terminals`**.
- Bind HTTP to `0.0.0.0` and a non-colliding port when possible.
- Secrets stay in Cloud Secrets / env — never hardcode in this file.

See Cursor Cloud docs for the current schema if fields change.
