#!/usr/bin/env node
/**
 * stop — remind the agent to verify before claiming done.
 * Does not block; returns allow with an agent_message nudge.
 */

import { stdin } from "node:process"

const chunks = []
for await (const c of stdin) chunks.push(c)
// Drain stdin even if unused
void Buffer.concat(chunks)

process.stdout.write(
  JSON.stringify({
    continue: true,
    permission: "allow",
    agent_message:
      "Before claiming done: run verify-change (and npm run verify if you touched .cursor/ or scripts/). State the commands you ran.",
  }),
)
