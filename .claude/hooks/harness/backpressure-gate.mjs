#!/usr/bin/env node
// backpressure-gate.mjs - PreToolUse hook for Bash(git commit*)
// Purpose: Block commits if build/test/lint failed
// Exit 0 = allow, Exit 2 = block (uses stderr for messages)

import { readFileSync, existsSync, appendFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const input = readFileSync(0, 'utf-8');

let data;
try {
  data = JSON.parse(input);
} catch (e) {
  process.exit(0);
}

const cwd = data?.session_state?.cwd || process.cwd();
const stateDir = join(cwd, '.omc', 'harness-state');
if (!existsSync(stateDir)) mkdirSync(stateDir, { recursive: true });

const logFile = join(stateDir, 'hook-debug.log');

function log(msg) {
  const timestamp = new Date().toISOString();
  appendFileSync(logFile, `[${timestamp}] backpressure-gate: ${msg}\n`);
}

log('Hook started');

const command = data?.tool_input?.command || '';
log(`Command: ${command}`);

// Only check for git commit commands
if (!command.match(/\bgit commit\b/)) {
  log('Not a git commit, allowing');
  process.exit(0);
}

log('Git commit detected, checking backpressure status');

const statusFile = join(stateDir, 'backpressure-status');

if (!existsSync(statusFile)) {
  log('No status file, allowing with warning');
  console.error('HARNESS WARNING: No build/test verification recorded. Consider running tests first.');
  process.exit(0);
}

const status = readFileSync(statusFile, 'utf-8').trim();
log(`Status: ${status}`);

if (status === 'PASS') {
  log('Status is PASS, allowing');
  process.exit(0);
} else if (status === 'UNKNOWN') {
  log('Status is UNKNOWN, blocking');
  console.error('HARNESS BLOCK: Cannot commit. No build/test verification in this session.');
  console.error('Run build/test/lint and ensure they pass before committing.');
  process.exit(2);
} else {
  const failFile = join(stateDir, 'backpressure-last-fail');
  const lastFail = existsSync(failFile) ? readFileSync(failFile, 'utf-8').trim() : 'unknown';
  log(`Status is not PASS, blocking. Last fail: ${lastFail}`);
  console.error(`HARNESS BLOCK: Cannot commit. Last verification failed: ${lastFail}`);
  console.error('Run build/test/lint and ensure they pass before committing.');
  process.exit(2);
}
