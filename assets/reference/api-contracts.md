# API contracts

Conventions for HTTP APIs. Adapt field names to the stack, but keep one envelope.

## Response envelope

Prefer a single shape for JSON APIs:

```json
{ "ok": true, "data": { } }
```

```json
{ "ok": false, "error": { "code": "VALIDATION_ERROR", "message": "…", "details": [] } }
```

- Success and failure are distinguishable without guessing HTTP-only semantics.
- `code` is stable for clients; `message` is human-readable; `details` is optional and structured.

## Errors

| Kind | HTTP | Notes |
| --- | --- | --- |
| Validation | 400 | Schema failures; list fields |
| Authn | 401 | Missing/invalid credentials |
| Authz | 403 | Authenticated but not allowed |
| Not found | 404 | Unknown resource (avoid leaking existence when sensitive) |
| Conflict | 409 | Idempotency / unique constraint |
| Rate limit | 429 | Include retry guidance when possible |
| Unexpected | 500 | Log internals; do not return stacks to clients |

Map domain errors to this table in one place (middleware or a shared helper).

## Validation

- Validate at the boundary (body, query, path, headers).
- Prefer a schema library (Zod, Pydantic, etc.).
- Reject unknown fields when that is safer for your API.

## Pagination

Pick one and stick to it:

- Cursor: `?cursor=&limit=` → `{ items, nextCursor }`
- Offset: `?page=&pageSize=` → `{ items, page, pageSize, total? }`

Cap `limit` / `pageSize` server-side.

## Idempotency

- Safe methods are idempotent by nature.
- For creates/payments, accept an `Idempotency-Key` (or equivalent) and store the first result.
- Retries must not double-charge or double-create.

## Versioning

- Prefer additive changes.
- If breaking: URL prefix (`/v1`) or explicit version header — document in `AGENTS.md`.
