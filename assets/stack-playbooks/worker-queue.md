# Playbook: Worker / queue

Use when background jobs, retries, or async pipelines are the product (or a major slice).

## Scaffold

Do not invent a broker. Prefer what the deploy target already offers:

| Context | Starting point |
| --- | --- |
| Node on a PaaS | BullMQ + Redis, or the platform's queue |
| Python | Celery / RQ / ARQ + Redis, or cloud queue + worker process |
| Serverless | Queue trigger (SQS, etc.) + worker function |

Scaffold the **API or CLI that enqueues** and a **worker entrypoint** as two processes (or two services). Document both in `AGENTS.md`.

## Structure

- Explicit job payload schema (versioned)
- Idempotent handlers (at-least-once delivery is normal)
- Dead-letter / failure path and visibility timeout understood
- Separate `start` commands for API vs worker in Cloud `environment.json` / compose

## Verify

```bash
# Enqueue a test job, then assert the worker side effect (DB row, file, log line)
npm test   # or pytest
```

Manually: run worker, enqueue once, confirm exactly-once business effect under retry.

## Security

- Queue payloads are untrusted input — validate
- Workers use least-privilege credentials
- Do not put secrets in job bodies; pass IDs and load secrets from env
- Threat model the worker the same as an API (SSRF, injection via payload fields)

## After scaffold

- MCP: `context7`; observability MCP if they have one
- Compose/Docker examples: `assets/templates/docker/`
- Record broker choice in `decisions.mdc`
