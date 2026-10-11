# MCP catalog

Copy an entry into `.cursor/mcp.json` → `mcpServers`. Use the `add-mcp-server` skill.

Never paste secret values. Reload MCP in Cursor after editing. Cloud Agents also need dashboard / team MCP; laptop `~/.cursor/mcp.json` does not apply there.

Configs below match Cursor's project schema (`type` + `command` for stdio, `url` for HTTP). Vendor packages change — prefer the vendor's current docs if install fails.

## Platform note (stdio / npx)

Cursor spawns MCP servers **without a shell**. On **Windows**, bare `"command": "npx"` often fails with `spawn npx ENOENT` because `npx` is a `.cmd` shim. Use:

```json
"command": "cmd",
"args": ["/c", "npx", "-y", "some-package"]
```

On **macOS / Linux / Cloud Agent VMs**, use:

```json
"command": "npx",
"args": ["-y", "some-package"]
```

Stdio examples below use the Unix form (Cloud-friendly). Swap to the Windows form on Windows laptops.

## How to choose

| Need | Add |
| --- | --- |
| Library / framework docs | `context7` |
| GitHub PRs, issues, files | `github` |
| Issues / planning | `linear` or `atlassian` |
| Web deploy (Vercel) | `vercel` |
| Web deploy (Render) | `render` |
| Cloudflare / Workers | `cloudflare` |
| Postgres | `neon` or `supabase` |
| Auth + backend | `supabase` or `firebase` |
| Payments | `stripe` |
| Design | `figma` |
| Browser verification | `playwright` or `chrome-devtools` |
| Error tracking | `sentry` |
| Chat / comms | `slack` |
| Docs wiki | `notion` |
| Observability | `datadog` |
| SAST / code security | `semgrep` |
| Terraform / registry | `terraform` |
| Local files (constrained) | `filesystem` |
| Fetch URLs | `fetch` |
| Extra reasoning steps | `sequential-thinking` |

## context7

Use when the agent must look up current library docs.

```json
"context7": {
  "url": "https://mcp.context7.com/mcp",
  "headers": {
    "CONTEXT7_API_KEY": "${env:CONTEXT7_API_KEY}"
  }
}
```

Env: `CONTEXT7_API_KEY` (optional on the public endpoint; add if you have a key).

## github

```json
"github": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
  }
}
```

HTTP alternative (GitHub Copilot MCP):

```json
"github": {
  "url": "https://api.githubcopilot.com/mcp/",
  "headers": {
    "Authorization": "Bearer ${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
  }
}
```

Env: `GITHUB_PERSONAL_ACCESS_TOKEN`

## linear

```json
"linear": {
  "url": "https://mcp.linear.app/mcp",
  "headers": {
    "Authorization": "Bearer ${env:LINEAR_API_KEY}"
  }
}
```

Env: `LINEAR_API_KEY`

## atlassian

Jira / Confluence (Atlassian Rovo MCP). OAuth in Cursor.

```json
"atlassian": {
  "url": "https://mcp.atlassian.com/v1/mcp/authv2"
}
```

Prefer this HTTP URL over the legacy `/v1/sse` endpoint (SSE is unsupported for Cloud Agents and deprecated by Atlassian).

## vercel

```json
"vercel": {
  "url": "https://mcp.vercel.com"
}
```

OAuth is handled in Cursor. For tokens in CI / stdio tools, use `VERCEL_TOKEN` in Cloud Secrets.

## render

```json
"render": {
  "url": "https://mcp.render.com/mcp",
  "headers": {
    "Authorization": "Bearer ${env:RENDER_API_KEY}"
  }
}
```

Env: `RENDER_API_KEY`

## cloudflare

Broad Cloudflare API MCP (OAuth). Product-specific URLs also exist (`docs.mcp.cloudflare.com`, `bindings.mcp.cloudflare.com`, …) — enable only what you need.

```json
"cloudflare": {
  "url": "https://mcp.cloudflare.com/mcp"
}
```

## supabase

```json
"supabase": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@supabase/mcp-server"],
  "env": {
    "SUPABASE_ACCESS_TOKEN": "${env:SUPABASE_ACCESS_TOKEN}"
  }
}
```

Env: `SUPABASE_ACCESS_TOKEN` (and project refs as needed). Confirm the current package name in Supabase docs.

## neon

```json
"neon": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@neondatabase/mcp-server"],
  "env": {
    "NEON_API_KEY": "${env:NEON_API_KEY}"
  }
}
```

Env: `NEON_API_KEY`

## stripe

```json
"stripe": {
  "url": "https://mcp.stripe.com"
}
```

Or stdio:

```json
"stripe": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@stripe/mcp", "--tools=all"],
  "env": {
    "STRIPE_SECRET_KEY": "${env:STRIPE_SECRET_KEY}"
  }
}
```

Env: `STRIPE_SECRET_KEY` (test key for local).

## figma

```json
"figma": {
  "url": "https://mcp.figma.com/mcp",
  "headers": {
    "Authorization": "Bearer ${env:FIGMA_ACCESS_TOKEN}"
  }
}
```

Env: `FIGMA_ACCESS_TOKEN`

## playwright

Use for browser verification of a web UI.

```json
"playwright": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@playwright/mcp"]
}
```

## chrome-devtools

Alternative browser verification via Chrome DevTools Protocol.

```json
"chrome-devtools": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "chrome-devtools-mcp@latest"]
}
```

## sentry

Error tracking / issue triage. OAuth in Cursor.

```json
"sentry": {
  "url": "https://mcp.sentry.dev/mcp"
}
```

Optionally scope: `https://mcp.sentry.dev/mcp/{orgSlug}/{projectSlug}`.

## slack

```json
"slack": {
  "url": "https://mcp.slack.com/mcp",
  "headers": {
    "Authorization": "Bearer ${env:SLACK_BOT_TOKEN}"
  }
}
```

Env: `SLACK_BOT_TOKEN` (and usually a team/workspace install). Prefer OAuth in Cursor when available.

## notion

```json
"notion": {
  "url": "https://mcp.notion.com/mcp",
  "headers": {
    "Authorization": "Bearer ${env:NOTION_API_KEY}"
  }
}
```

Env: `NOTION_API_KEY`

## firebase

```json
"firebase": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "firebase-tools", "experimental:mcp"]
}
```

Auth is typically `firebase login` on the machine, or a service account via env. Do not commit service account JSON.

## datadog

```json
"datadog": {
  "url": "https://mcp.datadoghq.com/mcp",
  "headers": {
    "DD-API-KEY": "${env:DD_API_KEY}",
    "DD-APPLICATION-KEY": "${env:DD_APP_KEY}"
  }
}
```

Env: `DD_API_KEY`, `DD_APP_KEY`

## semgrep

SAST / security scanning. The hosted `mcp.semgrep.ai` endpoint and `uvx semgrep-mcp` are **deprecated**. Use the Semgrep CLI MCP (install Semgrep first).

```json
"semgrep": {
  "type": "stdio",
  "command": "semgrep",
  "args": ["mcp"],
  "env": {
    "SEMGREP_APP_TOKEN": "${env:SEMGREP_APP_TOKEN}"
  }
}
```

Env: `SEMGREP_APP_TOKEN` (optional for basic local scans; required for Semgrep App features). Confirm `semgrep` is on `PATH`.

## terraform

Official HashiCorp server (Docker). Not an npm package.

```json
"terraform": {
  "type": "stdio",
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "-e",
    "TFE_TOKEN",
    "hashicorp/terraform-mcp-server"
  ],
  "env": {
    "TFE_TOKEN": "${env:TFE_TOKEN}"
  }
}
```

Env: `TFE_TOKEN` (optional for public registry lookups; required for HCP Terraform / TFE). Requires Docker. Binary install alternative: see HashiCorp Terraform MCP docs.

## filesystem

Constrained local file access. **Pin allowed directories** — do not point at the whole disk.

```json
"filesystem": {
  "type": "stdio",
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-filesystem",
    "${workspaceFolder}"
  ]
}
```

## fetch

Fetch URL content as MCP tools.

**Risk:** unrestricted URL fetch can hit internal/metadata endpoints (SSRF from the agent host). Disable by default; enable only when the agent must retrieve public docs, and prefer scoped alternatives when available.

```json
"fetch": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-fetch"]
}
```

## sequential-thinking

Extra structured thinking steps for hard problems. Optional; enable only when useful.

```json
"sequential-thinking": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
}
```

## Custom HTTP server

```json
"my-service": {
  "url": "https://example.com/mcp",
  "headers": {
    "Authorization": "Bearer ${env:MY_SERVICE_TOKEN}"
  }
}
```

## Custom stdio server

Prefer per-key `${env:NAME}` over `envFile`. Loading the whole `.env` into an MCP child process widens blast radius if that process is compromised.

```json
"my-local": {
  "type": "stdio",
  "command": "node",
  "args": ["${workspaceFolder}/tools/mcp-server.js"],
  "env": {
    "MY_SERVICE_TOKEN": "${env:MY_SERVICE_TOKEN}"
  }
}
```

Optional (local only): `"envFile": "${workspaceFolder}/.env"` — stdio only; do not use for production-shaped MCP.
