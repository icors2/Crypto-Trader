# Recipe: Realtime

**Sensitive:** medium — auth on channels; do not broadcast private data.

## Goal

Client sees live updates for one resource (e.g. list refresh, presence, or chat message) without full page reload.

## Defaults (if unset)

- Use what the platform offers: Supabase Realtime, PartyKit, Pusher, Ably, Cloudflare Durable Objects, or SSE from your API.
- Prefer SSE/WebSocket behind your auth over a second unauthenticated public channel.

## Minimum slice

1. One channel/topic tied to a resource id.
2. Authz: only permitted users subscribe.
3. Server publishes on the write path that already mutates data.
4. Client reconnect / loading behavior documented.

Out of scope for v1: CRDT collaborative editing, multi-region fanout — unless asked.

## Security

- Authorize subscribe and publish.
- Do not put secrets in client-side realtime payloads.
- Rate-limit publish from clients if clients can emit.

## Verify

- Two clients (or two tabs): write in A, appear in B
- Logged-out or other-tenant user cannot subscribe

## MCP

Vendor MCP only if managing realtime config via tools.
