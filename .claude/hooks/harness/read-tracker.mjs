#!/usr/bin/env node
// read-tracker.mjs - PostToolUse hook for Read
// Purpose: Track which files have been read (for context-gate)

import { readFileSync, appendFileSync, mkdirSync, existsSync } from 'fs';
import { join } from 'path';

const input = readFileSync(0, 'utf-8');
let data;

try {
  data = JSON.parse(input);
} catch {
  process.exit(0);
}

const filePath = data?.tool_input?.file_path || data?.tool_input?.filePath;
if (!filePath) process.exit(0);

const cwd = data?.session_state?.cwd || process.cwd();
const stateDir = join(cwd, '.omc', 'harness-state');
const readLogPath = join(stateDir, 'read-log.txt');

if (!existsSync(stateDir)) {
  mkdirSync(stateDir, { recursive: true });
}

const normalizedPath = filePath.replace(/^[A-Za-z]:/, '').replace(/\\/g, '/');
appendFileSync(readLogPath, filePath + '\n');
appendFileSync(readLogPath, normalizedPath + '\n');

process.exit(0);
