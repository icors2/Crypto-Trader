# Feature recipes

Read by the `add-integration` skill. Copy patterns into the app; do not paste secrets.

| Recipe | When | Sensitive? |
| --- | --- | --- |
| [auth.md](auth.md) | Login, sessions, OAuth, magic links | Yes |
| [database.md](database.md) | Postgres or other durable store | Yes if multi-tenant |
| [payments.md](payments.md) | Stripe / billing | Yes |
| [file-upload.md](file-upload.md) | Images, docs, blobs | Yes |
| [email.md](email.md) | Transactional email | Medium |
| [ai-feature.md](ai-feature.md) | Chat, completions, embeddings | Yes (keys + data) |
| [realtime.md](realtime.md) | Live updates, presence | Medium |
| [seed-data.md](seed-data.md) | Demo content so the UI is not empty | No |
| [analytics.md](analytics.md) | Product analytics | Medium (PII) |

User-level vendor skills (Supabase, Neon, Stripe, Vercel, Cloudflare, …) may exist on a laptop but are **invisible to Cloud Agents**. Prefer these recipes plus `assets/mcp-catalog.md`.

Defer exact package versions to current vendor docs (`context7` MCP when enabled).
