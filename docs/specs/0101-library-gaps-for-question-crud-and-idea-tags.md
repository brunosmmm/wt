---
id: SPEC-0101
title: "Library gaps for question CRUD and idea tags"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
parent: SPEC-0098
milestone: "M5: interactive desk"
source_idea: IDEA-131
tags: [ideas, explore, org]
---

## Context

Child of [SPEC-0098](./0098-light-ideas-tui-beside-classic-cli.md) (IDEA-131). Today
`explore` supports `add_question`, `resolve_question(s)`, and bulk `set_questions`, but not
unresolve / edit-one / delete. Tags are set only at `add_idea` capture — no mutator. The
mutation desk (SPEC-0102) must not invent these in the UI layer.

## Goals / Non-goals

**Goals**
- Library APIs (+ thin CLI if natural) for: unresolve question, edit one question's text,
  delete one question (1-based index, same addressing as resolve).
- Optional: set per-question priority `[#A|B|C]`; reorder is nice-to-have, not required for
  desk v1 if delete+add suffices.
- `set_idea_tags` (or equivalent) to replace/set tags on an existing idea headline.
- Tests covering drift/re-resolve behavior consistent with existing writers.

**Non-goals**
- TUI wiring (SPEC-0102).
- Stable question UUIDs (v1 stays 1-based index).
- Changing OPEN|RESOLVED vocabulary.

## Decision

Extend `explore.py` / `org_write.py` with the missing mutators before SPEC-0102 ships.
Expose on `wt idea questions` where it fits (`--unresolve`, `--edit`, `--delete`) and
`wt idea` tag subcommand or flags — keep CLI thin. Addressing remains 1-based index into
`read_idea_questions` order.

## Design

**As shipped.** All four question mutators land in `explore.py`; the tag mutator in
`org_write.py`. `set_question_priority` was in scope after all — it fell out of the shared
plumbing for free.

- `unresolve_question(cfg, selector, index)` — flip to OPEN; text and cookie preserved.
- `edit_question(cfg, selector, index, text)` — replace text, keep state + cookie. Empty text
  raises rather than silently deleting: `delete_question` is the way to remove one.
- `delete_question(cfg, selector, index)` — remove one headline. Deleting the last one leaves an
  *empty* section, not a missing one, so later `--add` has somewhere to land.
- `set_question_priority(cfg, selector, index, priority)` — set or (with `None`) clear `[#A|B|C]`.
- `set_idea_tags(cfg, selector, tags)` — rewrite only the headline's trailing `:tag:tag:` block,
  so the state keyword and `[#A]` cookie survive **by construction** rather than by re-parsing.
  De-dups (first occurrence wins), strips stray colons, validates against org's `[\w@-]` set.

*Two shared helpers* keep the contract identical across the four index-addressed mutators:

- `_question_at(cfg, selector, index)` validates **before** any write — so a bad index cannot
  half-apply. It also rejects `bool` explicitly: Python makes `True == 1`, so `index=True` would
  otherwise silently edit question #1.
- `_write_questions(...)` ensures the `#+TODO: OPEN | RESOLVED` header, **re-resolves the task
  when that insert shifted line numbers**, then rewrites the section.

Both paths go through `_atomic_backup_write`; `set_idea_tags` carries the same
`expected state != found state` drift guard as `set_idea_priority`, and stamps `:UPDATED:`.

*CLI (thin).* `wt idea questions` gains `--unresolve N`, `--edit N --text …`, `--delete N`,
`--priority N --pri A|B|C|none`; the existing "exactly one action" guard was extended to cover
them, and `--edit`/`--priority` fail fast when their companion flag is missing. New
`wt idea tags SELECTOR --set "a, b"` (comma **or** space separated; `--set ""` clears) — a
whole-set replace, which the help text says out loud.

## Alternatives considered

- **Desk uses only `set_questions` full replace** — rejected; too footgun-prone for interactive
  edit.
- **Stable question IDs** — deferred; not required for v1.

## Acceptance criteria

- [x] Unresolve / edit / delete question work via library (+ CLI) with tests.
- [x] `set_idea_tags` works via library (+ CLI) with tests.
- [x] Invalid index raises `ValueError` with no write (same spirit as resolve).
- [x] No TUI code required to mark this spec done.

## Test plan

**Executed 2026-07-30.** New sibling file `tests/test_question_crud.py` — 53 tests.

- **Automated tests:** unresolve (incl. cookie preserved, open→open no-op); edit (state + cookie
  preserved, empty text refused); delete (re-indexing of the rest, last-one leaves empty
  section); priority set/clear + invalid letter; `set_idea_tags` replace / clear / de-dup /
  colon-strip / invalid tag / state+cookie preserved / survives a `retitle_idea` round-trip;
  a **parametrised no-write matrix** — 4 mutators × 8 bad indices (`0, -1, 4, 99, "2", None,
  1.0, True`) each asserting the file is byte-identical afterwards; non-idea selector rejected;
  CLI round-trip, flag-combo guards, clean error (no traceback) on a bad index, and
  `wt ideas --tag` (SPEC-0089) seeing tags written by the new mutator.
- **Manual verification:** on a throwaway idea in an isolated `WT_CONFIG_DIR`/`WT_DATA_DIR` —
  add ×3 → resolve 2 → unresolve 2 → edit 1 → priority 3 A → delete 2 → tags `tui, ideas`, then
  read the org file directly: `*** OPEN reworded first?` / `*** OPEN [#A] third question?` and
  `* IDEA throwaway for 0101 :tui:ideas:`. Bad index → `Error: no question #9 (idea has 2)`,
  exit 1; `--set "no/slash"` → `invalid tag`, exit 1.
- **Regression guard:** `uv run pytest` — 841 passed, including the pre-existing
  `test_questions_state.py` / resolve / normalize suites.

## Clock Log

`wt idea clock-in/out` on IDEA-131 (org LOGBOOK, not mirrored here).

## Rollout / migration

Can land in parallel with SPEC-0099/0100. **Blocks** SPEC-0102.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none)
