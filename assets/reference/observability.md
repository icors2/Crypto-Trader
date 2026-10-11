# Observability

Minimum bar for apps agents deploy or operate.

## Structured logging

- Log JSON (or key=value) with: timestamp, level, message, `requestId` / `correlationId`.
- Never log passwords, tokens, session IDs, or raw PII.
- Use levels honestly: error for failed requests you care about; debug for local only.

## Correlation

- Accept or create a request ID at the edge; pass it through services and into logs.
- Include it in error responses when safe (helps support without leaking internals).

## Health endpoints

- `GET /health` (or framework equivalent): process up.
- `GET /ready` when you have deps: DB/queue reachable. Fail readiness if the app should leave the load balancer.

## Metrics and traces (when you add them)

- RED: rate, errors, duration for key endpoints.
- Trace outbound calls (DB, HTTP) with the same correlation ID.
- Prefer one vendor already in the project's MCP/deploy story (e.g. Datadog) over inventing a stack.

## Alerting

Alert on: error rate spikes, latency SLO burn, health/ready failures, queue lag, certificate expiry.

Do not alert on every log line. Noise trains people to ignore pages.

## Agent checklist

- [ ] Request ID on HTTP paths
- [ ] No secrets/PII in logs
- [ ] Health (and ready if stateful)
- [ ] Failures visible in whatever MCP/observability the project enabled
