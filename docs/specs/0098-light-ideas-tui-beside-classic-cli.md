---
id: SPEC-0098
title: "Light ideas TUI beside classic CLI"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: epic
milestone: "M5: interactive desk"
source_idea: IDEA-128
tags: [tui, ideas, explore, cli]
---

## Context

Promoted from `IDEA-128` after a feasibility pass over the CLI/library boundary and an
explicit disposition of every OPEN question (all resolved on the idea Log).

**Problem.** Human triage of ideas and open questions is one-shot Rich tables plus discrete
CLI writes. There is no light interactive desk for navigate / expand / mutate while keeping
classic `wt`.

**What exists.** Click + Rich one-shot commands; versioned JSON (`wt.ideas.v1`, `wt.idea.v1`,
`wt.hub.v1`); clean library mutators in `explore.py` / `org_write.py`; agent surface =
`--json` + skills ([SPEC-0053](./0053-defer-mcp-until-skills-and-hub-json-prove.md)). Prior
TUI mentions were **narrow non-goals**: [SPEC-0023](./0023-human-workflow-docs-wt-next-hints.md)
(no dashboard rewrite for workflow docs) and
[SPEC-0035](./0035-pretty-wt-idea-show-via-rich-and-pygments-with.md) (no full org fold/images
editor via IDEA-043). This epic is a **new** governing design for a light explore desk — not
a silent reopen of those rejects.

**Child ideas already parked (do not re-seed duplicates):** IDEA-129…IDEA-134.

## Goals / Non-goals

**Goals**

- Ship an optional interactive **ideas/explore desk** entered via `wt tui`.
- Preserve classic Click+Rich CLI and agent `--json` / skills unchanged.
- Reuse existing library read/write APIs; no dual write semantics.
- Cover list/filter/search, detail (Summary / questions / Log), explore mutations, light
  metadata + clock, JSON parity for clock/open-Q counts, and an optional read-only hub tab.

**Non-goals**

- Promote / generate / export wizards inside the TUI.
- Spec markdown authxxing, Cursor-skill judgment, or MCP.
- Full org editor / fold / images (SPEC-0035 non-goal stands).
- Time reports, topic mapping, meetings ingest.
- Hub as a write surface; replacing `--json` as the agent contract.
- Making bare `wt` (no subcommand) interactive.
- File locking / flock (drift guard + refresh UX only).

## Decision

Deliver a **Textual** optional extra (`wt[tui]`, pin `textual>=8,<9`) and a `wt tui` Click
command that hosts a minimal two-pane **ideas explore desk**. The desk calls the same Python
APIs as the CLI (`collect_idea_tasks`, `idea_show_payload`, `append_log`, question mutators,
etc.). Classic install without Textual keeps working; missing Textual on `wt tui` exits with
an install hint.

Locked product decisions (from IDEA-128):

1. Pin Textual to major 8 (`>=8,<9`).
2. Load **all** ideas; UI switch shows/hides non-active (closed/archived/terminal).
3. Extend **`wt.idea.v1`** (and list rows if useful) with clock + per-idea open-Q count —
   shared JSON for TUI and agents.
4. Library question CRUD (unresolve / edit / delete, plus tags) **lands before** the mutation
   desk (IDEA-131 before IDEA-132).

## Architecture / cross-cutting design

```
wt tui  →  report (lists/hub) + explore (enrichment) + org_write (mutations)
classic CLI  →  same libraries
skills / agents  →  classic CLI + --json only
```

**Invariants children must respect**

- **One mutator path.** TUI never shells out to `wt` and never invents write rules outside
  `explore` / `org_write`.
- **Post-write refresh.** After every mutation: re-`resolve_selector` + reload enrichment;
  surface drift `ValueError` as refresh/retry UX.
- **Questions.** Address by 1-based index matching `resolve_question` unless a later child
  introduces stable IDs (not required for v1).
- **JSON additive only.** Schema version stays `wt.idea.v1` / row envelopes; new fields are
  additive and tested in existing JSON CLI tests.
- **Optional dep.** Runtime hard-deps stay click/rich/pyyaml/orgparse; Textual only via
  optional extra.
- **Visual restraint.** Two-pane, minimal chrome; no dashboard widget sprawl; next-step hints
  are display-only (no `wt next --do`).

## Breakdown / sub-specs

Existing child ideas (IDEA-129…134); titles match for seed-children idempotency if re-run.
All Meta-Tools / internal.

- [x] [SPEC-0099](./0099-optional-textual-packaging-and-wt-tui-entry.md) — Optional Textual
      packaging and `wt tui` entry (IDEA-129) — **done**
- [x] [SPEC-0100](./0100-read-only-ideas-list-and-detail-desk.md) — Read-only ideas list and
      detail desk (IDEA-130) — **done**
- [x] [SPEC-0101](./0101-library-gaps-for-question-crud-and-idea-tags.md) — Library gaps for
      question CRUD and idea tags (IDEA-131) — **done**
- [x] [SPEC-0102](./0102-explore-mutations-in-the-tui-desk.md) — Explore mutations in the TUI
      desk (IDEA-132) — **done**
- [x] [SPEC-0103](./0103-metadata-clock-and-idea-json-parity-for-the-desk.md) — Metadata, clock,
      and idea JSON parity (IDEA-133) — **done**
- [x] [SPEC-0104](./0104-optional-read-only-hub-triage-tab.md) — Optional read-only hub triage
      tab (IDEA-134) — **done**

Sequencing: **129 → 130**; **131 parallel** with 129/130; **132 after 131+130**; **133** after
desk (JSON can land with or just before metadata UI); **134 last** (optional).

## Acceptance criteria

- [x] `wt tui` launches the ideas desk when Textual is installed; clear error when not.
- [x] Classic CLI commands and `--json` schemas remain green; base install needs no Textual.
- [x] Desk can browse all ideas with a non-active visibility switch; expand Summary /
      questions / Log; mutate via library APIs (log, summary, full question CRUD, metadata,
      clock) with post-write refresh.
- [x] `wt.idea.v1` (and list rows) exposes clock + open-Q count.
- [x] Optional hub tab is read-only over `hub_payload`; no promote/export in-TUI.
- [x] All child specs `done`.

## Test plan

- **Integration/e2e tests:** optional-extra import path; headless/pilot Textual smoke for
  list→detail→one mutation→refresh; JSON schema tests for additive clock/open-Q fields;
  full `uv run pytest` without Textual still passes (TUI tests gated or in optional CI job).
- **Manual verification:** `uv sync --extra tui` (or equivalent); `wt tui`; toggle non-active;
  resolve a question; clock in/out; confirm `wt idea show --json` shows new fields; confirm
  `wt ideas` / bare `wt` unchanged without the extra.
- **Regression guard:** pre-existing CLI/JSON tests; no change to default dependency set.

## Rollout / sequencing

1. Accept this epic + children (no implementation in the accept session).
2. Implement 129 → 130; parallel 131; then 132 → 133; optional 134.
3. Partial delivery: packaging alone is a no-op UI; read-only desk is useful alone; mutations
   require 131.

**Shipped 2026-07-30**, in that order, across four commits. Final surface — `wt tui`
(optional `wt[tui]` extra):

```
ideas | hub                    tabs (h)
  list: id st p k q upd idea   q = open questions, ◕ = clock running
  detail: Summary / Questions / Log / next-step hint
  j k / a r          browse · search · non-active · refresh
  l s ? c t x        log · summary · questions · capture · retitle · explored
  m i X              metadata · clock toggle · close
```

Deliberately **not** shipped, per the epic's non-goals: promote / generate / export wizards,
spec authxxing, file locking, hub writes, and bare `wt` becoming interactive.

## Definition of done

- [x] All child specs `done` (the linter gates this).
- [x] Integration test plan executed; `uv run pytest` green — **877 passed**; base install
      without the extra: 781 passed / 7 skipped, and `wt tui` exits 1 with an install hint.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

(none — all resolved on IDEA-128 before accept)
