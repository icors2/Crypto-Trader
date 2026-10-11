---
name: setup-vm
description: Stand up the paper crypto day-trader on a Linux VM or local host. Use when cloning onto a new machine, deploying for paper testing, writing .env, running Docker Compose, or the user asks for setup.
---

# Setup the paper trader on a VM

Follow [SETUP.md](../../../SETUP.md) from the repo root. Do not improvise a different stack.

## When to use

- User asks to set up, install, deploy to a VM, or get the bot running for paper testing
- A new clone is missing `.env`, Docker, or a healthy `/healthz`
- Another agent needs a runbook with verification gates

## Preconditions

- Target is Linux (or the operator can run Docker)
- You can run commands on that machine
- Operator agrees this host stays **paper** (`mode: paper`)

## Steps

1. Open `SETUP.md` and execute sections **1 → 6** in order.
2. Prefer **Path A (Docker)** on a VM. Use Path B only if Docker is unavailable.
3. Create `.env` on disk. Never commit it. Never paste secret values into chat, rules, or skills.
4. Leave `ROBINHOOD_*` unset. Do not edit `config/config.yaml` to `live`.
5. Bind the host port to `127.0.0.1:8000`. Use Tailscale or SSH `-L` for remote access.
6. Stop only when every checkbox in **SETUP.md → Verification** is true.

## Verify

- `GET /healthz` is HTTP 200 and `"ok": true` (paused counts as healthy)
- Login works; `/` shows Paper account; `/settings` shows paper ledger controls
- `git check-ignore -q .env` succeeds
- `mode` is still `paper`

## Failure modes

- Wrong branch / sparse checkout → `src/crypto_trader/app.py` missing; see SETUP.md §2
- `/healthz` 503 → loop not heartbeating; read compose/uvicorn logs; do not set `START_LOOP=0`
- SQLite permission denied in Docker → `chown 10001:10001 config data`
- Publishing `0.0.0.0` on a public NIC → bind loopback instead

## Related

- After setup, operator knobs: Admin UI (paper cash, risk, STOP)
- Live trading: `go-live` skill — not this one
- Deploy URL wording: `deploy-app` is vendor-agnostic; this project is local Docker / Tailscale
