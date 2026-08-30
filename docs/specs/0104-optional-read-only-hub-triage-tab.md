---
id: SPEC-0104
title: "Optional read-only hub triage tab"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
parent: SPEC-0098
depends_on: [SPEC-0099, SPEC-0100]
milestone: "M5: interactive desk"
source_idea: IDEA-134
tags: [tui, hub]
---

## Context

Child of [SPEC-0098](./0098-light-ideas-tui-beside-classic-cli.md) (IDEA-134).
[SPEC-0052](./0052-wt-hub-json-union-of-ideas-internal-specs.md) /
[SPEC-0092](./0092-hub-tasks-today-slice.md) shipped `wt hub --json` and deferred a Rich hub
table. A read-only TUI tab can fill the human triage gap without mutating hub.

## Goals / Non-goals

**Goals**
- Optional tab/pane in `wt tui` consuming `hub_payload` (ideas + today/tasks slice as
  configured).
- Navigate hub ideas into the existing detail pane (SPEC-0100).
- Display-only hints toward classic CLI for promote/export (no wizards).

**Non-goals**
- Hub as a write surface (SPEC-0052 non-goal stands).
- Filtering hub internal/outbound arrays beyond what `hub_payload` already supports
  ([SPEC-0096](./0096-filter-parity-for-wt-next-hub-and-agenda.md)).
- Promote/generate/export in-TUI.
- Replacing `wt hub --json` for agents.

## Decision

Add a read-only hub triage tab that calls `hub_payload` and reuses desk navigation into idea
detail. Specs/outbound rows are informational; actions are copyable CLI hints at most.

## Design

**As shipped.** `TabbedContent` with `ideas` (the SPEC-0100 two-pane desk, unchanged) and
`hub`; `h` toggles between them.

- `model.load_hub(cfg, tasks_slice=…, **filters)` flattens `hub_payload` (`wt.hub.v1`) into
  `[HubLine]` + a one-line summary. No Textual, so the whole tab is testable on a base install.
- Sections in payload order: **ideas · internal specs · outbound · tasks(slice)**. The section
  label prints once per group rather than on every row — repeating it would be four columns of
  noise. The summary carries the aggregates (`43 ideas · 5 internal · 27 outbound · 5 stale ·
  18 with open Qs`).
- Idea rows reuse the SPEC-0103 fields in their meta cell (project · `N open q` · `◕ clocked
  in`), so the hub and the desk tell the same story.
- **Only idea rows carry an `idea_id`.** Spec rows can't be drilled — there is nothing in the
  ideas desk to show for them — so they surface a copyable `wt spec generate|export <ID>` hint
  via `notify()` instead. A test asserts exactly that split, and another asserts no
  `promote_idea` / `scaffold_outbound` / `generate_from_spec` / `export_spec` symbol is
  reachable from either desk module.
- Drilling switches to the ideas tab and reloads on that id; if the hub listed an idea the
  current view hides, the non-active switch is flipped on rather than landing on nothing.
- Hub filters are the desk's opening filters minus `sort`/`desc` (list-only concepts).
- Item text is clipped to a **measured** budget, same rule the ideas list learned: unclipped
  titles pushed the `meta` column clean off the right edge, silently hiding it rather than
  shrinking it. `on_resize` re-clips the hub too, without re-reading.

## Alternatives considered

- **Rich hub table in CLI** — still deferred; TUI is the chosen human surface here.
- **Mutating hub** — rejected.

## Acceptance criteria

- [x] Hub tab renders `hub_payload` data without writes.
- [x] User can drill from a hub idea into idea detail.
- [x] No promote/export mutation from the tab.
- [x] `wt hub --json` unchanged for agents.

## Test plan

**Executed 2026-07-30.** `tests/test_tui_hub.py` — 11 tests (8 need no Textual).

- **View model:** every section flattened; summary counts; `tasks_slice` honoured for
  `today`/`open`/`none`; idea rows surface the SPEC-0103 `N open q` meta.
- **Read-only:** `load_hub` twice leaves the org file byte-identical; browsing the tab in a
  pilot (`j`/`j`/`k`/`enter`) likewise; `wt hub --json` still emits `wt.hub.v1` with its
  original keys.
- **Drill split:** every `ideas` row has an `idea_id` and every non-idea row has `None`; spec
  rows carry a `wt spec generate SPEC-NNNN` hint string; no promote/export/generate symbol
  appears in `app.py` or `model.py`.
- **Pilot:** `h` opens the tab and the grid shows a seeded idea, a seeded spec title and the
  summary; `enter` on an idea row switches back to the ideas tab with that id selected; `h`
  toggles back.
- **Manual verification:** rendered against the live org at 115×24 — 43 ideas / 5 internal /
  27 outbound / 5 stale / 18 with open Qs, section label printed once per group, meta showing
  project + open-Q counts + `◕ clocked in` on IDEA-134 (the idea clocked in for this spec).
  That render is what caught the `meta` column being pushed off-screen.
- **Regression guard:** `uv run pytest` — 877 passed, `tests/test_hub.py` green.

## Clock Log

`wt idea clock-in/out` on IDEA-134 (org LOGBOOK, not mirrored here).

## Rollout / migration

Last child; optional. Desk remains useful without it.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none)
