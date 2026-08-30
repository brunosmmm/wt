---
id: SPEC-0103
title: "Metadata, clock, and idea JSON parity for the desk"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
parent: SPEC-0098
depends_on: [SPEC-0099, SPEC-0100]
milestone: "M5: interactive desk"
source_idea: IDEA-133
tags: [tui, json, clock, ideas]
---

## Context

Child of [SPEC-0098](./0098-light-ideas-tui-beside-classic-cli.md) (IDEA-133). Desk needs
kind/priority/workstream/close and clock in/out. Epic Q3 decided these signals also belong
in shared JSON — not TUI-only `Task` reads.

## Goals / Non-goals

**Goals**
- Desk actions: set kind, priority, workstream; close drop/researched; clock-in / clock-out
  via existing `org_write` / `explore` APIs.
- Extend `wt.idea.v1` (`idea_show_payload`) with clock status (at least open-clock boolean
  and/or intervals) and per-idea open-question count.
- Extend list `idea_row` (and thus `wt.ideas.v1` / search / next as applicable) with the same
  additive fields when cheap and useful for the list pane.
- Tests for JSON shape in existing JSON CLI tests.

**Non-goals**
- flock / file locking.
- Changing clock semantics beyond current `clock_in` / `clock_out`.
- A TUI-only data path that bypasses JSON builders.

## Decision

Prefer extending `idea_show_payload` / `idea_row` additively under existing schema names
(`wt.idea.v1`, `wt.ideas.v1`, …). TUI consumes those builders for display and uses library
mutators for writes. Wire desk UI for metadata + clock after or alongside JSON fields.

## Design

**As shipped.** Three additive fields, on **both** `idea_show_payload` (`wt.idea.v1`) and
`idea_row` (so `wt.ideas.v1`, `wt next`, `wt hub` inherit them). Schema strings unchanged.

| field | type | meaning |
|---|---|---|
| `open_questions` | int | questions not RESOLVED; **always present**, `0` rather than omitted |
| `clock_open` | bool | a clock is running *right now* (a `Task.clock` entry with no end) |
| `clocked_hours` | float | sum of **closed** intervals only, rounded to 4dp |

- `explore.clock_fields(task)` is the single definition, shared by both builders — no drift
  between "what `wt ideas --json` says" and "what `wt idea show --json` says" (there is a test
  asserting the two agree).
- **An open interval contributes 0 hours**, matching `report._clocked_hours`. A running session
  must never inflate a total.
- No `clock: [{start, end}]` list: the Design floated it, but nothing in the desk or the epic
  needs per-interval data, and `Task.clock` already exposes it to any caller that does. Omitted
  rather than shipped unused.
- **Cost of `open_questions` on list rows** is one enrichment read per row. Measured over the
  live 43-idea corpus: `wt ideas --json` 0.583s before, 0.579s after — no measurable cost, so
  it is unconditional. It saves agents an `idea show` round-trip per row.

*Desk UI.* A single `ChoiceScreen` (pick one from a short closed list) serves kind / priority /
workstream / close-outcome, so adding a field later costs a call site rather than more chrome:

- `m` → field list → value list (`set_idea_kind` / `set_idea_priority` / `set_idea_workstream`)
- `i` → **one key both directions**; the payload's `clock_open` already says which way it goes
- `X` → close (`drop` / `researched`)
- `apply_mutation` gained `kind` / `priority` / `workstream` / `tags` / `close` / `clock_in` /
  `clock_out`, so these follow the same one-mutator-path rule as SPEC-0102.

*Surfacing.* A `q` column carries the open-question count (blank at zero — a column of `0`s is
noise). A running clock marks the **id cell** with `◕` rather than getting its own column: it is
the one piece of state you can forget you left on. Non-clocked ids are padded two spaces so the
column still aligns. The detail header gains `◕ clocked in · N.NNh logged`. `r`/refresh moved to
`show=False` to keep the footer inside 110 columns.

## Alternatives considered

- **TUI-only Task.clock reads** — rejected (epic Q3).
- **Schema version bump to v2** — rejected unless additive fields prove insufficient; prefer
  additive v1.

## Acceptance criteria

- [x] `wt idea show ID --json` includes clock + open-question count fields.
- [x] List JSON rows include open-Q count (and clock indicator if specified in Design at ship).
- [x] Desk can change kind/priority/workstream, close, and clock in/out.
- [x] JSON tests cover the new fields; agents benefit without using the TUI.

## Test plan

**Executed 2026-07-30.** `tests/test_clock_json_parity.py` — 13 tests (10 need no Textual).

- **`wt.idea.v1`:** schema string still `wt.idea.v1` with the three fields present;
  `clock_open` flips across `clock-in` / `clock-out`; `clocked_hours` sums two seeded closed
  intervals to exactly 2.5h and **stays 2.5h while a third is open**; an idea with no questions
  reports `0`, not a missing key.
- **Row parity:** `wt ideas --json` rows carry the same fields; `idea_row` and
  `idea_show_payload` are asserted to agree on `open_questions`; `wt next --json` and
  `wt hub --json` inherit them via the shared builder.
- **Desk wiring:** `kind` / `priority` / `workstream` / `tags` / `clock_in` / `clock_out` /
  `close` through `apply_mutation`, each read back from the payload; `DeskRow` exposes
  `open_questions` + `clock_open`.
- **Pilot:** `i` toggles the clock **both** directions; `m` → priority → B lands on the org
  headline; the rendered grid shows the `q` count, the `◕` marker and `clocked in`.
- **Manual verification:** rendered against the live 43-idea org at 110×18 — `q` column shows
  real counts (6, 10, 5, 4, 11), `◕` correctly marks IDEA-133 (the idea clocked in during this
  spec) and no other row, detail reads `clock idle · 0.10h logged` for the selected idea.
  Timing measured before/after on the same corpus (0.583s → 0.579s).
- **Regression guard:** `uv run pytest` — 866 passed; the pre-existing `test_json_cli.py`
  schema tests accept the additive fields unchanged.

## Clock Log

`wt idea clock-in/out` on IDEA-133 (org LOGBOOK, not mirrored here).

## Rollout / migration

JSON fields can land before desk bindings. Desk bindings need SPEC-0099/0100; mutations
overlap SPEC-0102 sequencing (may land after 0102 for less UI thrash).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none)
