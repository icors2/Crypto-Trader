#!/usr/bin/env node
/**
 * Scan tracked files for likely secrets.
 * Usage: node scripts/scan-secrets.mjs
 *
 * Suppress a line with: pragma: allowlist secret
 */

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const MAX_FILE_BYTES = 1_500_000;
const ALLOW = /pragma:\s*allowlist\s+secret/i;

const BINARY_EXT =
  /\.(png|jpe?g|gif|webp|ico|pdf|zip|gz|tgz|bz2|xz|7z|woff2?|ttf|eot|mp[34]|wav|mov|avi|exe|dll|so|dylib|bin|lock)$/i;

/** @type {{ name: string, re: RegExp }[]} */
const patterns = [
  { name: "AWS access key", re: /\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/g },
  { name: "GitHub PAT (classic)", re: /\bghp_[A-Za-z0-9]{20,}\b/g },
  { name: "GitHub OAuth/App token", re: /\bgho_[A-Za-z0-9]{20,}\b/g },
  { name: "GitHub server-to-server", re: /\bghs_[A-Za-z0-9]{20,}\b/g },
  { name: "GitHub fine-grained PAT", re: /\bgithub_pat_[A-Za-z0-9_]{20,}\b/g },
  { name: "OpenAI / sk- key", re: /\bsk-[A-Za-z0-9]{20,}\b/g },
  { name: "OpenAI project key", re: /\bsk-proj-[A-Za-z0-9_-]{20,}\b/g },
  { name: "Anthropic key", re: /\bsk-ant-[A-Za-z0-9_-]{20,}\b/g },
  { name: "npm token", re: /\bnpm_[A-Za-z0-9]{20,}\b/g },
  { name: "Slack token", re: /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/g },
  { name: "Stripe live secret", re: /\bsk_live_[A-Za-z0-9]{10,}\b/g },
  { name: "Stripe test secret", re: /\bsk_test_[A-Za-z0-9]{10,}\b/g },
  { name: "Stripe live publishable", re: /\bpk_live_[A-Za-z0-9]{10,}\b/g },
  { name: "Google API key", re: /\bAIza[0-9A-Za-z\-_]{20,}\b/g },
  { name: "PEM private key", re: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/g },
  {
    name: "JWT",
    re: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g,
  },
];

const ASSIGN =
  /(?:^|[\s"'`])(?:(?:export|set)\s+)?([A-Z][A-Z0-9_]{2,})\s*[=:]\s*['"]?([^\s'"]{12,})['"]?/g;

const SECRETISH_NAME =
  /(?:SECRET|TOKEN|PASSWORD|PASSWD|API[_-]?KEY|PRIVATE[_-]?KEY|ACCESS[_-]?KEY|AUTH|CREDENTIAL|CONNECTION[_-]?STRING|DATABASE_URL|REDIS_URL|MONGO(?:DB)?_URI)/i;

function listedFiles() {
  try {
    const out = execFileSync("git", ["ls-files", "-z"], {
      cwd: root,
      encoding: "buffer",
      maxBuffer: 32 * 1024 * 1024,
    });
    return out
      .toString("utf8")
      .split("\0")
      .filter(Boolean)
      .map((f) => f.replace(/\//g, "\\") === f ? f : f); // keep git paths as-is
  } catch {
    return null;
  }
}

function entropy(s) {
  if (!s) return 0;
  const freq = new Map();
  for (const c of s) freq.set(c, (freq.get(c) || 0) + 1);
  let h = 0;
  const n = s.length;
  for (const count of freq.values()) {
    const p = count / n;
    h -= p * Math.log2(p);
  }
  return h;
}

function isPlaceholder(value) {
  return (
    /^(true|false|null|undefined|none|changeme|replace|your[_-]?|xxx|todo|example|dummy|test|localhost|127\.0\.0\.1)/i.test(
      value,
    ) ||
    /\$\{env:[A-Z0-9_]+\}/.test(value) ||
    /^<.*>$/.test(value) ||
    /^\[.*\]$/.test(value)
  );
}

function scanText(rel, text) {
  /** @type {{ file: string, line: number, name: string, snippet: string }[]} */
  const hits = [];
  const lines = text.split(/\r?\n/);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (ALLOW.test(line)) continue;

    for (const { name, re } of patterns) {
      re.lastIndex = 0;
      if (re.test(line)) {
        hits.push({
          file: rel,
          line: i + 1,
          name,
          snippet: line.trim().slice(0, 120),
        });
      }
    }

    ASSIGN.lastIndex = 0;
    let m;
    while ((m = ASSIGN.exec(line)) !== null) {
      const [, key, value] = m;
      if (!SECRETISH_NAME.test(key)) continue;
      if (isPlaceholder(value)) continue;
      if (entropy(value) < 3.2 && !/[A-Za-z0-9+/]{20,}/.test(value)) continue;
      hits.push({
        file: rel,
        line: i + 1,
        name: `High-entropy assignment (${key})`,
        snippet: line.trim().slice(0, 120),
      });
    }
  }

  return hits;
}

function main() {
  const files = listedFiles();
  if (!files) {
    console.error("scan-secrets: git ls-files failed; is this a git repo?");
    process.exit(2);
  }

  /** @type {{ file: string, line: number, name: string, snippet: string }[]} */
  const findings = [];

  for (const rel of files) {
    if (BINARY_EXT.test(rel)) continue;
    if (rel.startsWith("assets/templates/hooks/")) continue; // example payloads may look secret-like
    const full = join(root, rel);
    if (!existsSync(full) || !statSync(full).isFile()) continue;
    let st;
    try {
      st = statSync(full);
    } catch {
      continue;
    }
    if (st.size > MAX_FILE_BYTES) continue;

    let text;
    try {
      text = readFileSync(full, "utf8");
    } catch {
      continue;
    }
    if (text.includes("\0")) continue;

    findings.push(...scanText(relative(root, full).replace(/\\/g, "/"), text));
  }

  if (findings.length === 0) {
    console.log("Secret scan: PASS (0 findings)");
    process.exit(0);
  }

  console.log(`Secret scan: FAIL (${findings.length} finding(s))`);
  console.log("");
  for (const f of findings) {
    console.log(`  - ${f.file}:${f.line}  [${f.name}]`);
    console.log(`    ${f.snippet}`);
  }
  console.log("");
  console.log(
    "Suppress a false positive on a line with: pragma: allowlist secret (review before allowing).",
  );
  console.log(
    "Note: this scan covers tracked files only (git ls-files), not history or untracked files. Prefer Gitleaks in CI for history.",
  );
  process.exit(1);
}

main();
