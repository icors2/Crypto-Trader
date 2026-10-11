#!/usr/bin/env node
/**
 * beforeShellExecution — block destructive git, reckless deletes, and secret-file dumps.
 * Reads JSON from stdin; writes permission JSON to stdout.
 */

import { stdin } from "node:process"

const chunks = []
for await (const c of stdin) chunks.push(c)
const raw = Buffer.concat(chunks).toString("utf8").replace(/^\uFEFF/, "") || "{}"

let payload
try {
  payload = JSON.parse(raw)
} catch {
  process.stdout.write(
    JSON.stringify({
      continue: true,
      permission: "deny",
      user_message: "guard-shell hook: invalid JSON payload; denying command (fail closed)",
      agent_message:
        "beforeShellExecution hook could not parse stdin. Denying the command. Retry or ask the user.",
    }),
  )
  process.exit(0)
}

const command = String(payload.command || "")

const denyPatterns = [
  /\bgit\s+reset\s+--hard\b/i,
  /\bgit\s+clean\s+-[a-z]*f/i,
  /\bgit\s+(?:-[^\s]+\s+)*push\b[^\n]*\s--force\b/i,
  /\bgit\s+(?:-[^\s]+\s+)*push\b[^\n]*\s-f\b/i,
  /\bgit\s+(?:-[^\s]+\s+)*push\b[^\n]*\s\+[A-Za-z0-9_./:~-]+/i,
  /\brm\s+(-[a-zA-Z]*f[a-zA-Z]*r|--recursive).*[\\/]?(?:\.git|\/|\\\*|~)\b/i,
  /\brm\s+-rf\s+[\\/]/i,
  /\bRemove-Item\b[^\n]*-Recurse[^\n]*-Force[^\n]*[\\/]\s*$/i,
  /\b(?:cat|type|Get-Content|Get-Content\.exe)\b[^\n]*\.env\b(?!\.example)/i,
  /\b(?:cat|type|Get-Content)\b[^\n]*\.(?:pem|key)\b/i,
  /\b(?:cat|type|Get-Content)\b[^\n]*id_rsa\b/i,
]

const hit = denyPatterns.find((re) => re.test(command))

if (hit) {
  const msg = `Blocked by guard-shell hook: ${command.slice(0, 200)}`
  process.stdout.write(
    JSON.stringify({
      continue: true,
      permission: "deny",
      user_message: msg,
      agent_message:
        `${msg}. Use a safer alternative, or ask the user to run the destructive command themselves.`,
    }),
  )
  process.exit(0)
}

process.stdout.write(
  JSON.stringify({ continue: true, permission: "allow" }),
)
