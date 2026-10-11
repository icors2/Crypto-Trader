# Setup guide (for an AI agent)

Stand up this **paper-by-default** crypto day-trader on a Linux VM or local host. Follow the steps in order. Do not skip a verification gate. Do not invent a second stack.

This file is the source of truth for first-time setup. The Cursor skill `.cursor/skills/setup-vm/SKILL.md` points here.

## Goal

When you are done, all of these are true:

1. The repo is checked out on the target machine.
2. `.env` exists on disk, is **not** committed, and contains real values (never paste those values into chat, git, rules, or skills).
3. `config/config.yaml` has `mode: paper`.
4. The process is running and **`GET /healthz` returns HTTP 200** with `"ok": true` after the first heartbeat (paused is healthy).
5. The operator can log in at `http://127.0.0.1:8000`, see paper cash on `/`, and open `/settings`.
6. `mode` is still `paper`. You did **not** enable live Robinhood trading.

## Non-negotiables

- Never commit `.env`, private keys, passwords, session secrets, or Robinhood credentials.
- Never write secret **values** into `SETUP.md`, skills, rules, `mcp.json`, or the PR body. Names only.
- Never set `mode: live` during setup. Live has its own bar: `.cursor/skills/go-live/SKILL.md`.
- Bind the HTTP server to loopback on the host (`127.0.0.1:8000`). Reach it with Tailscale, `tailscale serve`, or an SSH tunnel. Do not publish `0.0.0.0` on a public NIC.
- Money is `Decimal`. Do not change SQLite money columns to REAL.
- Indicators come from Coinbase Exchange public candles. Do not add unofficial Robinhood clients or Gemini.

## Facts the agent needs

| Item | Value |
| --- | --- |
| Repo | `https://github.com/icors2/Crypto-Trader` |
| SSH | `git@github.com:icors2/Crypto-Trader.git` |
| Product branch until `main` contains `src/crypto_trader/` | `cursor/crypto-day-trader-bot-99ae` |
| Listen | `127.0.0.1:8000` |
| Health | `GET /healthz` — HTTP 200 healthy (including paused), HTTP 503 loop dead/stale |
| Config (directory mount) | `config/config.yaml` |
| SQLite | `data/trader.db` (WAL; ephemeral container FS is not enough) |
| Halt file | `data/STOP` |
| Timezone | `America/Chicago` (`tzdata` required) |
| Stack | Python 3.12, FastAPI/Uvicorn, uv, SQLite, Docker optional |
| Verify | `npm run verify` (needs Node + uv) |

Egress the box must allow (HTTPS):

- `https://api.exchange.coinbase.com` — candles + ticker (paper and live)
- `https://trading.robinhood.com` — **live only**; not required for paper
- `https://ntfy.sh` — optional alerts if `NTFY_TOPIC` is set

## Path choice

Use **Path A (Docker)** on a VM that should survive reboot.

Use **Path B (uv on the host)** when Docker is missing, or when you need to run pytest on that machine.

Do not run both on the same port.

---

## 1. Preconditions

On the target machine, confirm tools. Stop and install anything missing.

```bash
uname -a
command -v git
command -v curl
```

**Path A also needs:**

```bash
command -v docker
docker compose version
```

**Path B also needs** Python 3.11+ (3.12 preferred) and [uv](https://docs.astral.sh/uv/):

```bash
python3 --version
command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh
# then ensure ~/.local/bin is on PATH
```

Node is only required for `npm run verify`, not for running the bot.

Ask the operator (once) for:

- A UI password, **or** permission to generate one and show it a single time
- Whether they want ntfy alerts (`NTFY_TOPIC`)
- Confirmation this host is paper-only

Do not ask for Robinhood keys on a paper VM.

---

## 2. Clone the correct ref

```bash
git clone https://github.com/icors2/Crypto-Trader.git
cd Crypto-Trader
git fetch origin
```

Choose the ref that actually contains the bot:

```bash
if git cat-file -e origin/main:src/crypto_trader/app.py 2>/dev/null; then
  git checkout main
  git pull origin main
else
  git checkout cursor/crypto-day-trader-bot-99ae
  git pull origin cursor/crypto-day-trader-bot-99ae
fi
```

Gate: `test -f src/crypto_trader/app.py` and `test -f config/config.yaml`. If either is missing, the checkout is wrong (sparse clone or wrong branch). Fix before continuing.

---

## 3. Create `.env` (untracked)

```bash
test -f .env || cp .env.example .env
```

`.env.example` lists **names only**. Write values into `.env`. Suggested generator (run from the repo root after Path B install, or with system Python):

```bash
python3 - <<'PY'
import secrets
print("UI_SESSION_SECRET=" + secrets.token_urlsafe(32))
print("# UI_PASSWORD=<ask operator or generate token_urlsafe(16) and tell them once>")
PY
```

Minimum `.env` for a paper VM (replace the placeholders; do not commit the file):

```dotenv
# Hard ceilings the Admin form cannot raise
MAX_NOTIONAL_USD=100
MAX_DAILY_LOSS_USD=50
MAX_WEEKLY_LOSS_USD=150
MAX_CUMULATIVE_LOSS_USD=300
MIN_POLL_INTERVAL_SEC=5

# Web UI
UI_PASSWORD=replace-with-operator-password
UI_SESSION_SECRET=replace-with-token-urlsafe-32
SECURE_COOKIES=false
BIND_HOST=127.0.0.1
PORT=8000

# Paths (host Path B). Docker compose overrides these to /app/config and /app/data.
DATA_DIR=data
CONFIG_DIR=config
```

Rules:

- Prefer `UI_PASSWORD_HASH` (bcrypt) over plaintext `UI_PASSWORD` if you can hash on the box. Either one works. If both are unset, the app **generates** a password and logs it once at startup — copy that to the operator immediately.
- Leave `ROBINHOOD_*` unset on a paper VM.
- `SECURE_COOKIES=true` only when the browser hits the UI over HTTPS (for example `tailscale serve`).
- `BIND_HOST=0.0.0.0` is correct **inside** the container (compose sets this). On a bare-metal Path B host, keep `127.0.0.1`.

To hash a password after `uv sync`:

```bash
uv run python -c "import bcrypt,getpass; p=getpass.getpass(); print(bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode())"
```

Put the hash in `UI_PASSWORD_HASH` and remove `UI_PASSWORD`.

Gate: `test -f .env` and `grep -q '^UI_SESSION_SECRET=.\+' .env`. Do not `cat .env` into the conversation.

---

## 4. Confirm paper config

```bash
grep -E '^(mode|symbol|timezone|paper_starting_cash):' config/config.yaml
```

Expected:

- `mode: paper`
- `symbol: BTC-USD` (or another `BASE-USD` pair Coinbase Exchange lists)
- `timezone: America/Chicago`
- `paper_starting_cash` present

Do not edit `mode` to `live`. Strategy knobs can wait until the UI is up.

Create the data directory and make it writable by the container user (`uid 10001` in the Dockerfile):

```bash
mkdir -p data
# Path A on Linux bind mounts:
# sudo chown -R 10001:10001 config data
```

If you cannot `chown`, use Path B instead of fighting volume permissions.

---

## 5A. Run with Docker (preferred on a VM)

`compose.yml` binds `127.0.0.1:8000`, mounts `./config` and `./data`, and restarts unless stopped.

```bash
docker compose up --build -d
docker compose ps
docker compose logs --tail=80
```

Gate:

```bash
# may be 503 for up to ~40s until the first heartbeat
for i in $(seq 1 20); do
  code=$(curl -s -o /tmp/healthz.json -w '%{http_code}' http://127.0.0.1:8000/healthz || true)
  echo "try $i -> $code $(cat /tmp/healthz.json 2>/dev/null)"
  [ "$code" = "200" ] && break
  sleep 3
done
test "$code" = "200"
```

`paused: true` is success (session closed or STOP file). `ok: false` after a minute is failure — read logs.

If SQLite errors mention read-only or permission denied, `chown 10001:10001` the bind mounts and recreate:

```bash
docker compose down
sudo chown -R 10001:10001 config data
docker compose up -d
```

---

## 5B. Run with uv on the host

```bash
uv sync --all-extras
uv run pytest
uv run uvicorn crypto_trader.app:app --host 127.0.0.1 --port 8000
```

Equivalent: `uv run crypto-trader serve --host 127.0.0.1 --port 8000`.

For a durable VM without Docker, install a systemd user or system unit that runs that command from the repo directory with `EnvironmentFile=/absolute/path/to/Crypto-Trader/.env`, `Restart=always`, and `WorkingDirectory` set to the repo. Do not background with a raw `nohup` if you can use systemd or compose.

Gate: same `/healthz` loop as Path A.

Optional compile check:

```bash
npm run verify
```

Skip `npm run verify` only when Node is not installed **and** you already ran `uv run pytest`.

---

## 6. Smoke the operator UI

Do this even if tests passed. Login cookie is httpOnly.

```bash
# expect 303 to / and a session cookie
curl -s -D - -o /dev/null -c /tmp/ct.ck -b /tmp/ct.ck \
  -X POST http://127.0.0.1:8000/login \
  --data-urlencode "password=THE_OPERATOR_PASSWORD"

curl -s -b /tmp/ct.ck http://127.0.0.1:8000/ | grep -E 'Paper account|Health|Cash'
curl -s -b /tmp/ct.ck http://127.0.0.1:8000/settings | grep -E 'Save paper account|Stop ATR|Reset paper account'
```

Replace `THE_OPERATOR_PASSWORD` from `.env` / the generated startup log. Do not echo it back in your summary.

Expected:

- Dashboard mentions **Paper account** and cash (default starting cash is `10000` until they change it).
- Admin has paper ledger controls: set cash, deposit, withdraw, holdings, reset.
- `/trades` loads.

If login returns 401, the password is wrong. If it returns 429, wait 15 minutes (5 attempts / 15 minutes).

Browser (when tools exist): log in, open `/`, `/trades`, `/settings`. Confirm paper cash. Do not flatten or reset unless the operator asked.

---

## 7. First operator actions (paper only)

Tell the operator, do not do these unless they asked:

1. Open Admin → **Paper account** and set starting cash / current cash / a deposit if `$10000` is the wrong book.
2. Leave **mode** on paper.
3. Optional: set `NTFY_TOPIC` and recreate the container / restart uvicorn to get halt/restart alerts.
4. Optional remote access: `tailscale serve` or `ssh -L 8000:127.0.0.1:8000 user@vm`. Then set `SECURE_COOKIES=true` if the browser uses HTTPS.

Halt / resume without the UI:

```bash
printf 'halt\n' > data/STOP          # block new entries
rm -f data/STOP                      # plus Admin → Resume for weekly/cumulative
```

A container restart does **not** clear a weekly/cumulative halt. That needs **Resume** (or Admin → reset risk).

---

## 8. Persistence checklist

| Data | Where | Survives container recreate? |
| --- | --- | --- |
| Paper cash, holdings | `data/trader.db` tables `paper_account`, `paper_holdings` | Yes, if `./data` is mounted or on the host |
| Trades, positions, quotes | `data/trader.db` | Yes |
| Strategy knobs | `config/config.yaml` | Yes, if `./config` is mounted |
| Halt | `data/STOP` | Yes |
| Secrets | `.env` | Host file; not in the image |

The container filesystem is ephemeral. Never store the DB only inside the image.

Backup before risky experiments:

```bash
sqlite3 data/trader.db ".backup data/trader.backup.db"
cp config/config.yaml "config/config.yaml.bak"
```

---

## 9. Update the VM later

```bash
cd Crypto-Trader
git fetch origin
git pull --ff-only
# Path A
docker compose up --build -d
# Path B: restart uvicorn / systemd
```

Re-run the `/healthz` gate. Config and DB stay on the bind mounts.

---

## 10. Rollback

1. `docker compose down` (or stop systemd/uvicorn).
2. Check out the previous known-good git SHA.
3. Restore `data/trader.db` from `.backup` if the schema or ledger was damaged.
4. Restore `config/config.yaml.bak` if YAML was broken.
5. Start again and hit `/healthz`.

---

## Verification (do not claim setup complete until all pass)

- [ ] Correct git ref; `src/crypto_trader/app.py` exists
- [ ] `.env` present and untracked (`git check-ignore -q .env`)
- [ ] `config/config.yaml` still `mode: paper`
- [ ] `GET /healthz` → 200 and `"ok": true`
- [ ] Login succeeds; dashboard shows Paper account
- [ ] Admin shows Save paper account / deposit / reset
- [ ] No Robinhood private key in git (`git grep` must not find `ROBINHOOD_PRIVATE_KEY=`)
- [ ] You did not print `.env` contents in chat

---

## Failure modes

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `src/crypto_trader` missing | Sparse checkout or wrong branch | `git sparse-checkout disable` or checkout the product branch |
| `/healthz` 503 forever | Loop died, no heartbeat, or `START_LOOP=0` | Read logs; do not set `START_LOOP=0` on a VM |
| Healthcheck fail, UI up | Trading thread crashed; Docker marks unhealthy | Logs + `restart: unless-stopped`; unexpected loop errors exit 1 |
| Login 401 | Wrong password / hash | Reset `UI_PASSWORD` or `UI_PASSWORD_HASH`; restart |
| Login 429 | Rate limit | Wait; 5 tries / 15 minutes |
| SQLite / read-only | Bind mount owned by root | `chown 10001:10001 config data` |
| `ZoneInfoNotFoundError` | Missing `tzdata` | Image already installs it; Path B: `sudo apt-get install -y tzdata` |
| No candles / stale quote | Egress blocked to Coinbase | Allow `api.exchange.coinbase.com:443` |
| Settings save detaches config | File bind-mount of a single YAML | Mount the **`config/` directory**, not one file |
| Weekly halt after reboot | Counters persist in memory? weekly halt is in-process | Resume in Admin; restart does not mean “resume” |
| Paper cash reset on restart | Old image without ledger persist | Pull this branch; cash lives in SQLite |
| Accidental live | `mode: live` without keys | Process refuses to boot without `ROBINHOOD_*`; keep paper |

---

## Out of scope for this guide

- Flipping `mode: live` — use `.cursor/skills/go-live/SKILL.md` after the go-live bar.
- Public internet exposure without Tailscale/HTTPS.
- Changing hard ceilings above what the operator set in `.env`.
- Adding Gemini, unofficial Robinhood libraries, or a different UI framework.
