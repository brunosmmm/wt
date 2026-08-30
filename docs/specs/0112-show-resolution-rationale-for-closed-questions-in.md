---
id: SPEC-0112
title: "Show and capture question rationale in the desk and wt idea show"
status: done
owner: user
created: 2026-07-31
updated: 2026-07-31
kind: feature
depends_on: [SPEC-0111]
milestone: "M5: interactive desk"
source_idea: IDEA-142
tags: [tui, questions, org]
---

## Context

From `IDEA-142`: the questions modal lists RESOLVED questions but not *why* they were resolved.

**Three of the idea's four questions were answered by [SPEC-0111](./0111-question-section-round-trip-destroys-body-prose.md)
rather than by choosing:**

- *Where does rationale live?* In a **body** under the question headline — shipped, and
  round-trip-safe through every mutator.
- *Does this need stable question ids?* **No.** The body is attached **structurally**, by org
  nesting, not by index. Delete a question and its body goes with it; there is no
  position-keyed link to rot, so SPEC-0101's deferral stands.
- *Ship a view-only Log-beside-questions stopgap first?* **Moot** — real linkage now exists.

**So this spec is about display and capture, not data.** Verified 2026-07-31: `question_items`
in `wt.idea.v1` **already carries `body`** (SPEC-0111 gave it for free), but `format_idea_show`
drops it and the desk's `load_detail` flattens questions to plain strings. Nothing renders it.

## Goals / Non-goals

**Goals**
- The desk's questions modal shows a question's rationale beneath it.
- A dedicated key writes or edits a rationale, including on an already-resolved question.
- `wt idea show` renders rationales too — CLI/desk parity, the same call made for the `q` column.
- A library mutator owns the write, like every other desk mutation.

**Non-goals**
- Prompting for a rationale on every resolve (rejected below).
- Stable question ids — not needed.
- Rationale on the desk's *detail pane* question list; the modal is where questions are worked.
- Multi-paragraph editing UX beyond what the existing `BodyPrompt` gives.
- Backfilling rationales from existing Log entries — the convention was prose, and guessing the
  mapping would invent links that were never made.

## Decision

**`Enter` stays an instant toggle; a separate key (`r`) writes the rationale.** Bulk triage must
not pay a prompt on every resolve, and a separate action also covers the case a resolve-time
prompt cannot: attaching or fixing a rationale on a question resolved days ago.

Rationale is rendered in **both** surfaces. The data already exists in the JSON; only the two
text renderers drop it.

## Design

- **Library:** `set_question_body(cfg, selector, index, text)` in `explore.py`, addressed by the
  same 1-based index as every other question mutator (SPEC-0101), writing the `body` field
  SPEC-0111 introduced. Empty text clears the body.
- **Desk model:** `apply_mutation` gains a `question_body` action; `DeskDetail`'s question lists
  carry the body so the detail pane could render it later without another parse.
- **Desk modal:** `r` opens a `BodyPrompt` (multi-line, ctrl+s saves) pre-filled with any
  existing rationale. The rationale renders under its question, indented and dimmed, so the
  question list still scans as a list.
- **CLI:** `format_idea_show` indents the body under its question headline. `wt idea questions`
  gains `--body N --text …` for parity with the desk, so a rationale is writable without the TUI.

## Alternatives considered

- **Prompt on every resolve, Esc skips** — rejected: taxes every resolve including trivial ones,
  and still cannot attach a rationale after the fact.
- **Display-only, no capture in the desk** — rejected: the modal is exactly where you are when
  you decide, and org-editing by hand is the workflow this whole epic exists to avoid.
- **Rationale in the Log with a question reference** — rejected: that is today's broken
  convention, linked only by prose, and it rots when indices change.
- **Desk-only rendering** — rejected: recreates the CLI/desk divergence just closed for `q`.

## Acceptance criteria

- [x] A question with a rationale shows it in the desk's questions modal.
- [x] `r` writes a rationale, and can edit one on an already-resolved question.
- [x] `Enter` still resolves/reopens with no prompt.
- [x] `wt idea show` renders rationales under their questions.
- [x] `wt idea questions --body N --text …` writes one; empty text clears it.
- [x] The desk goes through `apply_mutation`; no new write path.
- [x] Question counts are unaffected (`q` column and `open_questions` ignore bodies).

## Test plan

**Executed 2026-07-31.** `tests/test_question_rationale.py` — 25 tests.

- **Library:** set / clear; a rationale on an **already-resolved** question (the case a
  resolve-time prompt cannot reach); a parametrised bad-index matrix (`0, -1, 3, 99, "2", None,
  True`) each asserting the file is byte-identical; the rationale survives resolve / unresolve /
  edit / priority; deleting a question takes its rationale with it — the structural attachment
  that made stable ids unnecessary.
- **CLI:** `--body N --text …` round trip and clear; `--body` without `--text` rejected;
  `--body` combined with `--edit` rejected rather than silently picking one, since both consume
  `--text`; `wt idea show` renders the body **indented** under its question; the JSON carries it
  and `open_questions` still reports 2, so a rationale cannot inflate the `q` column.
- **Desk:** `apply_mutation("question_body", …)` writes it; a source guard that `app.py` never
  names `set_question_body` directly.
- **Pilot:** the modal shows the rationale under its question and advertises `r`; `r` writes and
  then **edits**; `Enter` still resolves with **no prompt appearing** (asserted on the screen
  type, not just the state); Esc on the prompt leaves the file byte-identical.
- **Manual verification** in an isolated `WT_CONFIG_DIR`: wrote a rationale via the CLI, read it
  back through `wt idea show` and `--json`, cleared it, and rendered the modal at 96×22 — the
  rationale appears as `└ ANSI, hex was invisible on dark`, dim and indented under its question.
- **Regression guard:** `uv run pytest` — 995 passed; `test_question_bodies.py`,
  `test_question_crud.py` and `test_questions_state.py` green.

## Fixed along the way

`BodyPrompt` opened a pre-filled editor with the **cursor at position 0**, so editing an
existing rationale prepended — typing " so" onto "because" produced `"sobecause"`. Found by a
failing test rather than by review. The cursor now starts at the end, which also fixes the
Summary editor (`s`), pre-filled the same way.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — all four resolved on IDEA-142 before promotion)
