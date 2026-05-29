# Session Persistence

<!-- Inspired by ECC longform guide session storage patterns. Complements context_management.md (WHEN/WHAT to compact) with HOW/WHERE to persist and restore. -->

## Purpose

Concrete mechanisms for saving and restoring session state across compaction events and session boundaries. `context_management.md` governs when to compact and what to preserve; this file governs how to persist and where to store it.

---

## Persistence channels (what actually persists, and where)

Session state in this harness persists through three channels. Do **not** hand-author ad-hoc session-state files — that practice was never operationalized and the paths it named are owned by OMC.

- **Durable narrative → `sum` skill → `docs/sum/`.** The intentional, human-judged session summary: decisions, fixes/troubleshooting, what worked, what failed, what remains. Manual (see Decision below). This is the primary "resume context" artifact.
- **Runtime state → OMC-owned `.omc/state/`.** HUD, mission, subagent tracking (`.omc/state/`), per-session HUD (`.omc/state/sessions/<id>/`), and session-end telemetry (`.omc/sessions/<id>.json`) are written automatically by OMC's own hooks. These are OMC's namespace — do not write into them. Our harness's own state lives under `.omc/harness` (see `harness_integration_contract.md`).
- **Cross-session facts → auto-memory.** Durable user/project/feedback knowledge lives in the memory system, not in transient session files.

When capturing a phase boundary, fold the worked/failed/remaining detail into the `sum` summary — not a separate file.

---

## Decision: summarization stays manual (no PreCompact / Stop auto-save)

We deliberately do **not** run a `PreCompact` or `Stop` hook to auto-summarize sessions. Decided 2026-05-27.

- **PreCompact rarely fires.** In our usage a session seldom fills even ~50% of the context window, so a compaction-triggered hook would almost never run — low value for the maintenance cost.
- **Session end is not machine-detectable.** Only the user decides when a coherent thread of work is "done." A `Stop` hook fires when the assistant finishes a turn, not when the user closes out a session, so Stop-based auto-summary would misfire constantly.
- **The `sum` skill is manual by design.** Its value is the troubleshooting/decision narrative that is *not* already in git or the PR body; capturing that well requires the user's judgment about when the thread is complete.
- **Git-event triggers (push/merge) were considered and deferred.** `merge` is the only git event that means "this unit of work is accepted," but sessions and PRs are many-to-many (one session can span several PRs), so a merge-triggered full summary would fragment or duplicate. No good design yet — revisit only if a concrete, low-noise trigger emerges (e.g. a lightweight breadcrumb log rather than a full LLM summary).

If this is revisited, see `claudedocs/ecc_harness_analysis.md` (the original PreCompact proposal) and `docs/architecture/harness-architecture.md` §4.3 G7/G8.

---

## SHOULD: SessionStart context loading

A `SessionStart` hook can automatically surface relevant prior context. In this harness, `harness-version-check.mjs` reports harness drift at session start, and OMC's own session-restore loads prior runtime context. If resuming a specific thread, point yourself at the relevant `docs/sum/` summary rather than expecting an auto-loaded state file.

Keep loaded context minimal — only what's needed to resume, not full history.

---

## MAY: Dynamic system prompt injection

For mode-specific workflows, inject targeted context at session start:

```bash
# Load review-focused context
claude --system-prompt "$(cat .claude/contexts/review.md)"

# Load research-focused context
claude --system-prompt "$(cat .claude/contexts/research.md)"
```

Context files should be small (<100 lines) and focused on the specific workflow.

---

## MAY: Context aliases

Maintain named context profiles for common workflows:

| Alias | Context File | Use For |
|-------|-------------|---------|
| `dev` | `.claude/contexts/dev.md` | Active development (file paths, architecture) |
| `review` | `.claude/contexts/review.md` | Code review (standards, checklist refs) |
| `research` | `.claude/contexts/research.md` | Research mode (search patterns, MCP refs) |

---

## Relationship to Other Rules

- **`context_management.md`**: Governs WHEN to compact and WHAT to preserve. This file governs HOW and WHERE.
- **`learning_policy.md`**: Governs capturing reusable learnings. Session persistence covers the transient narrative (`sum` → `docs/sum/`); durable cross-session facts go to auto-memory.
- **`hook_recipes.md`**: Provides the hook mechanism; this file describes what to persist in those hooks.

---

## Self-Check

Before ending a session or compacting:

- [ ] Key decisions and file paths captured somewhere durable (not just in conversation memory)?
- [ ] Reusable facts pushed to auto-memory if they outlive this session?
- [ ] If the work thread is complete, run `/sum` to write the worked/failed/remaining narrative to `docs/sum/` (manual — see Decision above)?
