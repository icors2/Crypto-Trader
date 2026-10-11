---
name: add-mcp-server
description: Add or update a project MCP server in .cursor/mcp.json from the catalog. Use when the user needs a new tool integration, or during bootstrap when enabling GitHub, Linear, Vercel, Context7, Stripe, or similar.
---

# Add an MCP server

## Rules

- Project config is `.cursor/mcp.json`. Schema key is `mcpServers`.
- Never hardcode secrets. Use `${env:NAME}` in `env`, `headers`, and `auth`.
- `envFile` is **stdio only**.
- Enable servers the project will use. Do not add the whole catalog.
- Cloud Agents: prefer **HTTP**. SSE and `mcp-remote` are unsupported. Stdio runs inside the VM and exposes env to the agent.
- Same server name: project config overrides `~/.cursor/mcp.json`.
- Interpolation: `${env:NAME}`, `${workspaceFolder}`, `${userHome}`, `${workspaceFolderBasename}`.

## Steps

1. Read `assets/mcp-catalog.md` and pick an entry (or the vendor's current docs if the catalog is stale).
2. Read `.cursor/mcp.json`. Merge the new server; do not wipe existing ones.
3. Use this shape.

**stdio**

```json
{
  "mcpServers": {
    "example": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "some-mcp-package"],
      "env": {
        "API_KEY": "${env:API_KEY}"
      },
      "envFile": "${workspaceFolder}/.env"
    }
  }
}
```

**HTTP**

```json
{
  "mcpServers": {
    "example": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${env:EXAMPLE_TOKEN}"
      }
    }
  }
}
```

4. Add the env **names** to `.env.example` and to `.cursor/rules/memory.mdc` → Environment.
5. Tell the user to set the values in Cursor Settings → MCP / Cloud Secrets, and to reload MCP.
6. If `.cursor/mcp.json` is write-protected, print the merged JSON and ask them to save it.
7. Record why the server was added in `decisions.mdc` if it is a non-obvious choice.

## After adding

Remind the user: Cloud Agents do not inherit laptop MCP. Team/dashboard MCP may still be required at [cursor.com/agents](https://cursor.com/agents).
