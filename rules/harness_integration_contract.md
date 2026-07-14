# Harness Integration Contract

This document defines the repo-level contract for validating harness integration before an agent claims policy compliance.

## Hook Location

All hooks are in `.claude/hooks/harness/` and registered in `.claude/settings.json`.
Runtime state is stored in `.omc/harness-state/` (project-local, gitignored).
Hooks that emit a debug trace write it to `.omc/harness-state/hook-debug.log` **only when `HARNESS_DEBUG` is set to a non-empty value** (e.g. `HARNESS_DEBUG=1`); off by default, to avoid log noise. Not every hook logs there — `read-tracker`/`write-tracker` write only `read-log.txt`, and `kickoff-detector`/`harness-version-check` don't use it. Gate behavior — what blocks or allows — never depends on `HARNESS_DEBUG`.

## Required Gates and Hook Names

The following controls are required when harness is available:

1. `context-gate` hook — blocks edits to unread files (PreToolUse: Edit|Write)
2. `read-tracker` hook — records file reads for context-gate (PostToolUse: Read)
   - `write-tracker` hook — records files written for context-gate so a file created this session can be edited without re-reading (PostToolUse: Edit|Write)
3. `acceptance-gate` hook — blocks commits with unmet acceptance criteria (PreToolUse: Bash)
4. `backpressure-gate` hook — blocks commits if build/test/lint failed (PreToolUse: Bash)
5. `backpressure-tracker` hook — records build/test/lint results (PostToolUse: Bash)
6. `kickoff-detector` hook — reminds about kickoff for new work (UserPromptSubmit)
7. Architect verification — independent completion verification (oh-my-claudecode agent)

> The commit-only gates — `acceptance-gate`, `backpressure-gate`, and `review-gate` — are registered through a single dispatcher `commit-gates.mjs` (PreToolUse: Bash). It runs one `isGitCommit` check per Bash command and only invokes the three on an actual commit (one spawn instead of three on the common non-commit path). On a commit it runs all three in order and blocks if ANY blocks (each child gets a ~3s budget; a gate that fails to run cleanly is skipped with a loud `HARNESS WARNING`). `destructive-guard` stays a separate PreToolUse:Bash hook (it scans every command, not just commits).

> Scope drift is no longer hook-enforced (scope-gate retired). It is handled by the CLAUDE.md "Surgical Changes" rule + PR review; `out_of_scope` in seed.yaml is advisory prose the agent reads.

> **Task closeout** (`docs/rules/closeout_contract.md`): when a kickoff'd task lands on main (`compr`/`compush`), it is closed out — `seed.yaml` → `status: done`, `current-scope.md` retired, `task_closed` audit event. This is the **trigger lane** (best-effort, agent-run). The **verification lane** is independent: `docs-drift` warns (never fails) on inconsistent closeout state (orphan scope / half-closed / closeout-pending) at pre-push, not trusting the trigger. The acceptance-gate honors closed seeds (`done`/`superseded` → no active AC) and a `wip:`/`[wip]` commit bypasses unmet AC for in-progress checkpoints.

## Auxiliary Hooks and Orphan Detection

Not every `.mjs` in `.claude/hooks/harness/` is registered in `settings.json` directly. Two groups are intentionally indirect:

- **Helper modules** (imported by registered hooks, never registered themselves): `git-commit-detect` (shared `isGitCommit` detector used by `commit-gates`, `acceptance-gate`, `backpressure-gate`, `review-gate`), `risk-assess` (risk classification imported by `review-gate` and `backpressure-gate`), `backpressure-patterns` (shared by `backpressure-tracker` and `backpressure-failure-tracker`).
- **Standalone advisory / lifecycle hooks** (registered, non-blocking): `destructive-guard` (PreToolUse:Bash, scans every command), `mcp-gate` (advisory MCP-call notice), `backpressure-invalidator` (PostToolUse, marks state stale), `harness-version-check` (SessionStart).

`scripts/docs-drift` audits this layout. Its orphan check is **reachability-based**: a hook is "live" if it is registered in `settings.json` **or** reachable from a registered hook via an import / spawn reference (a quoted `*.mjs` literal that resolves to a real harness file). The delegated gates and the helper modules above are therefore live, not orphans. Only a hook that is unregistered **and** unreachable from any registered entry point is flagged — so a genuinely dead file left after a refactor is still caught. docs-drift is wired into `.githooks/pre-push` and blocks a push on FAIL-severity drift (broken links, a reference doc that claims `status: synced` while stale, a registered hook whose file is missing); WARNING-severity issues such as a true orphan, or an inconsistent closeout state (orphan current-scope / half-closed / closeout-pending), do not block.

## Gate Verification Requirements

Use concrete checks, not assumptions.

### 1) `context-gate` + `read-tracker` + `write-tracker`

- Files: `.claude/hooks/harness/context-gate.mjs`, `.claude/hooks/harness/read-tracker.mjs`, `.claude/hooks/harness/write-tracker.mjs`
- Log: `.omc/harness-state/hook-debug.log` (written only when `HARNESS_DEBUG` is set)
- State: `.omc/harness-state/read-log.txt` (appended by both `read-tracker` on Read and `write-tracker` on Edit|Write)

### 2) `acceptance-gate`

- File: `.claude/hooks/harness/acceptance-gate.mjs`
- Log: `.omc/harness-state/hook-debug.log` (written only when `HARNESS_DEBUG` is set)
- Reads: `docs/harness/current-scope.md` (checkboxes), `docs/harness/seed.yaml` (AC), `docs/harness/acceptance-done` (override flag)

### 3) `backpressure-gate` + `backpressure-tracker`

- Files: `.claude/hooks/harness/backpressure-gate.mjs`, `.claude/hooks/harness/backpressure-tracker.mjs`
- Log: `.omc/harness-state/hook-debug.log` (written only when `HARNESS_DEBUG` is set)
- State: `.omc/harness-state/backpressure-status`, `.omc/harness-state/test-history.json`
- **Known limitation**: `backpressure-tracker` runs on PostToolUse (success only). Claude Code does not invoke PostToolUse hooks on tool failure, so failed build/test/lint results are not recorded. `backpressure-gate` can only verify the presence of recent success, not detect failures directly.

### 4) `kickoff-detector`

- File: `.claude/hooks/harness/kickoff-detector.mjs`
- Reads: `docs/harness/kickoff-done` (suppresses reminder if exists)

### 5) Architect verification + Completion Attack Gate

- Provided by oh-my-claudecode `architect` agent
- Not a file hook — invoked via agent delegation
- **Extended by completion-attack gate** (see [`rules/adversarial_review.md`](adversarial_review.md)):
  - architect (기존 역할 유지) + security-reviewer + test-engineer 병렬 실행
  - 불일치 시 critic이 합의 판정
  - CRITICAL 발견 시 블로킹
- Output: `docs/harness/completion-attack-report.md`

## Startup Checklist (Run Before Claiming Compliance)

1. Confirm hooks directory exists: `test -d .claude/hooks/harness && echo hooks_ok`
2. Confirm all hook files are present:
   ```bash
   for h in context-gate read-tracker write-tracker commit-gates acceptance-gate backpressure-gate review-gate backpressure-tracker kickoff-detector; do
     test -f ".claude/hooks/harness/$h.mjs" && echo "$h: ok" || echo "$h: MISSING"
   done
   ```
3. Confirm settings.json registers the harness hooks: `grep -c "hooks/harness" .claude/settings.json` (non-zero; the exact count grows as gates are added — do not assert a constant)
4. Confirm Architect agent is available via oh-my-claudecode
5. Record harness status in your working notes and final PR report

## Fallback Behavior When a Gate Is Unavailable

If any required gate is unavailable, do not claim fully automated harness compliance for that gate. Apply this downgrade policy:

- Missing `context-gate`:
  - Downgrade from **MUST (automated pre-read enforcement)** to **manual pre-edit read checklist MUST**.
  - Record files read before each edit batch.
- Missing `acceptance-gate`:
  - Downgrade from **MUST (automated acceptance checks)** to **manual acceptance checklist MUST**.
  - Require explicit evidence section with commands, outputs, and file citations.
- Missing `backpressure-gate`:
  - Downgrade from **MUST (automated failure pressure)** to **manual stop-and-review MUST**.
  - After any failed verification, halt feature work until failure is resolved or explicitly risk-accepted.
- Missing Architect verification:
  - Downgrade from **MUST (independent verifier)** to **manual two-pass self-review MUST**.
  - Complete a second-pass review using `checklists/verify.md` before claiming done.

When downgrading, final report MUST include:

- Which gate was unavailable
- How manual checklist substitution was applied
- Remaining residual risk

## Known-Failure Matrix

| Symptom | Likely cause | Safe mitigation |
|---|---|---|
| Hook file not found in `.claude/hooks/harness/` | Partial clone or deleted hook file | Re-clone template or restore from git; if blocked, activate manual checklist downgrade |
| Hook exists but no events in `.omc/harness-state/hook-debug.log` | Debug logging is OFF by default (gated behind `HARNESS_DEBUG`) | An empty/absent log does NOT mean the hook is unregistered. Set `HARNESS_DEBUG=1` to enable logging, then verify settings.json entries and re-run a benign trigger. |
| `acceptance-gate` repeatedly blocks completion | Missing evidence or unchecked AC in `current-scope.md` | Check off completed criteria or create `docs/harness/acceptance-done` override |
| `backpressure-gate` loops on failures | Underlying failing test/check never addressed | Stop retries, fix root cause, then re-run once with documented rationale |
| `context-gate` blocks unexpectedly | `read-log.txt` missing or stale | Read the file first; if persistent, check read-tracker is registered in settings.json |
| Architect log missing for completed task | oh-my-claudecode not installed or architect agent unavailable | Run manual two-pass verification and mark Architect as downgraded in report |

## Copy-Paste Verification Template

Use this in PR descriptions or completion reports:

```md
### Harness Verification
- context-gate: [active | unavailable->manual] (evidence: `<command/log snippet>`)
- acceptance-gate: [active | unavailable->manual] (evidence: `<command/log snippet>`)
- backpressure-gate: [active | unavailable->manual] (evidence: `<command/log snippet>`)
- Architect verification: [active | unavailable->manual] (evidence: `<command/log snippet>`)

### Downgrades (if any)
- Gate: `<name>`
- Manual checklist used: `<checklist/steps>`
- Residual risk: `<brief note>`
```
