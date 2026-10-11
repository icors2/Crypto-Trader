#!/usr/bin/env node
/**
 * beforeReadFile — deny reading secret material into the agent context.
 */

import { stdin } from "node:process"
import { basename, normalize } from "node:path"

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
      user_message: "redact-read hook: invalid JSON payload; denying read (fail closed)",
      agent_message:
        "beforeReadFile hook could not parse stdin. Denying the read. Retry or ask the user.",
    }),
  )
  process.exit(0)
}

const filePath = String(
  payload.file_path || payload.filePath || payload.path || payload.file || "",
)
const norm = normalize(filePath).replace(/\\/g, "/")
const base = basename(norm)

const denied =
  /(^|\/)\.env$/i.test(norm) ||
  /(^|\/)\.env\.[^/]+$/i.test(norm) ||
  /\.pem$/i.test(norm) ||
  /\.key$/i.test(norm) ||
  /id_rsa$/i.test(base) ||
  /id_ed25519$/i.test(base) ||
  /credentials\.json$/i.test(base) ||
  /service[_-]?account.*\.json$/i.test(base)

if (denied && !/\.env\.example$/i.test(norm)) {
  const msg = `Blocked reading secret-like file: ${norm}`
  process.stdout.write(
    JSON.stringify({
      continue: true,
      permission: "deny",
      user_message: msg,
      agent_message:
        `${msg}. Ask the user for the needed env *names* or values via chat; do not read credential files.`,
    }),
  )
  process.exit(0)
}

process.stdout.write(
  JSON.stringify({ continue: true, permission: "allow" }),
)
