#!/usr/bin/env node
/**
 * Validate Cursor starter layout: rules, skills, MCP, and memory.
 * Usage: node scripts/audit-cursor-setup.mjs
 */

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const errors = [];
const warnings = [];

function walk(dir, predicate, acc = []) {
  if (!existsSync(dir)) return acc;
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, predicate, acc);
    else if (predicate(full, name)) acc.push(full);
  }
  return acc;
}

function read(path) {
  return readFileSync(path, "utf8");
}

function parseFrontmatter(text) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return null;
  const data = {};
  for (const line of match[1].split(/\r?\n/)) {
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    data[line.slice(0, idx).trim()] = line.slice(idx + 1).trim().replace(/^["']|["']$/g, "");
  }
  return data;
}

const secretLike =
  /(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|sk_(?:live|test)_[A-Za-z0-9]{10,}|ghp_[a-zA-Z0-9]{20,}|gho_[a-zA-Z0-9]{20,}|ghs_[a-zA-Z0-9]{20,}|github_pat_[a-zA-Z0-9_]{20,}|npm_[A-Za-z0-9]{20,}|xox[baprs]-[a-zA-Z0-9-]{10,}|(?:AKIA|ASIA)[0-9A-Z]{16}|AIza[0-9A-Za-z\-_]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)/;

// Required files
for (const rel of [
  "AGENTS.md",
  "README.md",
  ".cursor/mcp.json",
  ".cursor/rules/00-core.mdc",
  ".cursor/rules/10-memory-protocol.mdc",
  ".cursor/rules/20-security.mdc",
  ".cursor/rules/memory.mdc",
  ".cursor/rules/decisions.mdc",
  ".cursor/rules/conventions.mdc",
  ".cursor/rules/lessons.mdc",
  ".cursor/skills/security-review/SKILL.md",
  ".cursor/skills/verify-change/SKILL.md",
  ".cursor/skills/ship-change/SKILL.md",
  ".cursor/skills/scope-feature/SKILL.md",
  ".cursor/skills/deploy-app/SKILL.md",
  ".cursor/skills/debug-issue/SKILL.md",
  ".cursor/skills/checkpoint-rollback/SKILL.md",
  ".cursor/skills/add-integration/SKILL.md",
  ".cursor/skills/migrate-database/SKILL.md",
  ".cursor/skills/polish-ui/SKILL.md",
  ".cursor/agents/security-reviewer.md",
  "scripts/scan-secrets.mjs",
  "assets/checklists/security-review.md",
  "assets/checklists/definition-of-done.md",
  "assets/checklists/ui-polish.md",
  "assets/reference/threat-model.md",
  "assets/reference/cost-and-quotas.md",
  "assets/reference/ui-design.md",
  "assets/recipes/README.md",
  "assets/stack-playbooks/golden-path.md",
]) {
  if (!existsSync(join(root, rel))) errors.push(`Missing ${rel}`);
}

// Rules
const rulesDir = join(root, ".cursor/rules");
for (const file of walk(rulesDir, (_, name) => name.endsWith(".md"))) {
  errors.push(`Ignored by Cursor (use .mdc): ${relative(root, file)}`);
}
for (const file of walk(rulesDir, (_, name) => name.endsWith(".mdc"))) {
  const fm = parseFrontmatter(read(file));
  if (!fm) {
    errors.push(`Rule missing YAML frontmatter: ${relative(root, file)}`);
    continue;
  }
  const always = fm.alwaysApply === "true";
  if (!always && !fm.description && !fm.globs) {
    warnings.push(
      `Rule has no description/globs and alwaysApply is not true (manual @-mention only): ${relative(root, file)}`,
    );
  }
}

// Memory snapshot
const memoryPath = join(root, ".cursor/rules/memory.mdc");
if (existsSync(memoryPath)) {
  const memory = read(memoryPath);
  if (!/Status:/i.test(memory)) errors.push("memory.mdc has no Status field");
  if (/unbootstrapped/i.test(memory)) {
    warnings.push("memory.mdc Status is still unbootstrapped");
  }
}

// Skills
const skillsDir = join(root, ".cursor/skills");
if (!existsSync(skillsDir)) {
  errors.push("Missing .cursor/skills/");
} else {
  for (const name of readdirSync(skillsDir)) {
    const skillDir = join(skillsDir, name);
    if (!statSync(skillDir).isDirectory()) continue;
    const skillFile = join(skillDir, "SKILL.md");
    if (!existsSync(skillFile)) {
      errors.push(`Skill folder missing SKILL.md: .cursor/skills/${name}`);
      continue;
    }
    const fm = parseFrontmatter(read(skillFile));
    if (!fm) {
      errors.push(`Skill missing frontmatter: .cursor/skills/${name}/SKILL.md`);
      continue;
    }
    if (!fm.name) errors.push(`Skill missing name: .cursor/skills/${name}/SKILL.md`);
    else if (fm.name !== name) {
      errors.push(`Skill name "${fm.name}" must match folder "${name}"`);
    }
    if (!fm.description) errors.push(`Skill missing description: .cursor/skills/${name}/SKILL.md`);
  }
}

// MCP
const mcpPath = join(root, ".cursor/mcp.json");
if (existsSync(mcpPath)) {
  let mcp;
  try {
    mcp = JSON.parse(read(mcpPath));
  } catch (err) {
    errors.push(`mcp.json is not valid JSON: ${err.message}`);
  }
  if (mcp) {
    if (!mcp.mcpServers || typeof mcp.mcpServers !== "object") {
      errors.push("mcp.json must have an mcpServers object");
    } else {
      for (const [name, server] of Object.entries(mcp.mcpServers)) {
        if (!server || typeof server !== "object") {
          errors.push(`MCP server ${name} is not an object`);
          continue;
        }
        const blob = JSON.stringify(server);
        if (secretLike.test(blob)) {
          errors.push(`MCP server ${name} looks like it contains a hardcoded secret`);
        }
        const hasStdio = server.command || server.type === "stdio";
        const hasHttp = Boolean(server.url);
        if (!hasStdio && !hasHttp) {
          errors.push(`MCP server ${name} needs command (stdio) or url (HTTP)`);
        }
        if (server.envFile && !hasStdio) {
          warnings.push(`MCP server ${name}: envFile is stdio-only`);
        }
        if (
          server.command === "npx" &&
          process.platform === "win32"
        ) {
          warnings.push(
            `MCP server ${name}: bare command "npx" often fails on Windows (use cmd /c npx)`,
          );
        }
      }
    }
  }
}

// .env.example — names only (no KEY=value assignments with non-empty values)
const envExample = join(root, ".env.example");
if (existsSync(envExample)) {
  const lines = read(envExample).split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line || line.startsWith("#")) continue;
    const m = line.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (m && m[2].length > 0) {
      errors.push(
        `.env.example must list names only (found assigned value at line ${i + 1}: ${m[1]})`,
      );
    }
  }
}

// Optional project hooks — validate shape if present
const hooksPath = join(root, ".cursor/hooks.json");
if (existsSync(hooksPath)) {
  let hooks;
  try {
    hooks = JSON.parse(read(hooksPath));
  } catch (err) {
    errors.push(`hooks.json is not valid JSON: ${err.message}`);
  }
  if (hooks) {
    if (hooks.version !== 1 && hooks.version !== "1") {
      warnings.push("hooks.json: expected version 1");
    }
    if (!hooks.hooks || typeof hooks.hooks !== "object") {
      errors.push("hooks.json must have a hooks object");
    } else {
      for (const [hookName, list] of Object.entries(hooks.hooks)) {
        if (!Array.isArray(list)) {
          errors.push(`hooks.json hooks.${hookName} must be an array`);
          continue;
        }
        for (const entry of list) {
          if (!entry || typeof entry !== "object") continue;
          if (entry.command) {
            const cmd = String(entry.command);
            const scriptMatch = cmd.match(/(?:^|\s)(\.cursor\/hooks\/\S+\.mjs)/);
            if (scriptMatch) {
              const scriptRel = scriptMatch[1];
              if (!existsSync(join(root, scriptRel))) {
                errors.push(`hooks.json references missing script: ${scriptRel}`);
              }
            }
          }
        }
      }
    }
  }
}

// AGENTS.md placeholder vs status
const agentsPath = join(root, "AGENTS.md");
if (existsSync(agentsPath) && existsSync(memoryPath)) {
  const agents = read(agentsPath);
  const memory = read(memoryPath);
  const active = /\*\*Status:\*\*\s*active/i.test(memory);
  const placeholder = /Status: not bootstrapped/i.test(agents);
  if (active && placeholder) {
    errors.push("memory.mdc is active but AGENTS.md Project-specific section is still the placeholder");
  }
}

// Scan tracked-looking cursor files for secrets
for (const file of [
  ...walk(join(root, ".cursor"), (_, name) => name.endsWith(".mdc") || name.endsWith(".md") || name.endsWith(".json")),
  join(root, ".env.example"),
]) {
  if (!existsSync(file)) continue;
  if (secretLike.test(read(file))) {
    errors.push(`Possible hardcoded secret in ${relative(root, file)}`);
  }
}

const ok = errors.length === 0;
console.log(ok ? "Cursor setup audit: PASS" : "Cursor setup audit: FAIL");
if (errors.length) {
  console.log("\nErrors:");
  for (const e of errors) console.log(`  - ${e}`);
}
if (warnings.length) {
  console.log("\nWarnings:");
  for (const w of warnings) console.log(`  - ${w}`);
}
process.exit(ok ? 0 : 1);
