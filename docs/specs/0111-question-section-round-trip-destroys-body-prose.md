---
id: SPEC-0111
title: "Preserve question bodies: mode-aware parsing of the Open questions section"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-31
kind: feature
depends_on: [SPEC-0101]
milestone: "M5: interactive desk"
source_idea: IDEA-143
tags: [org, questions, bug, data-integrity]
---

## Context

From `IDEA-143`. Prose written under a `*** OPEN` question in `ideas.org` is destroyed by the
next question mutation, and in the common case it also **corrupts addressing**.

**Reproduced 2026-07-30** on shipped code, in an isolated config:

| body style | after an unrelated `--resolve 2` |
|---|---|
| unindented | becomes its **own phantom question**, shifting every later index — `--resolve 2` flipped the *prose*, while the real question 2 stayed open |
| indented | silently **absorbed into the question's text**: `*** OPEN alpha? indented rationale here` |

**It is worse than one idea at a time.** `wt idea normalize-questions` is lossy the same way,
and with no selector it walks **every idea in every idea-bearing file** — so one maintenance
command can convert stray prose into phantom questions corpus-wide in a single pass.

**Why it matters.** Hand-editing the org files is a premise of `wt`, not an edge case. A human
writing a note under a question is entirely reasonable, and both outcomes are silent. The
addressing corruption is the serious half: a *correct* `--resolve 2`, from the CLI or the desk,
mutates the wrong question.

**The rule is deliberate, which is why this needs a spec.** [SPEC-0054](./0054-open-questions-state-model.md)
treats a bare line as an OPEN question **on purpose**, to migrate legacy files where questions
really were bare bullets. It cannot simply be deleted.

## Goals / Non-goals

**Goals**
- Prose under a question in an already-normalized section is **preserved as a body**.
- Index addressing counts questions only — never prose — so `--resolve N` cannot hit the wrong
  item.
- Legacy migration keeps working: in an un-normalized section, bare lines are still questions.
- `normalize-questions` stops promoting prose.

**Non-goals**
- Stable question ids (SPEC-0101's deferral stands; see *Alternatives*).
- Surfacing bodies in the TUI questions modal — that is `IDEA-142`, which this unblocks.
- Changing the `OPEN|RESOLVED` vocabulary or the 1-based addressing contract.
- Repairing files already corrupted by this bug (see *Rollout*).

## Decision

**Mode-aware parsing.** `_classify_question_lines` gains a notion of whether the section is
already normalized — every question expressed as a `*** OPEN|RESOLVED` headline:

- **Normalized section:** non-headline lines are a **body** belonging to the preceding question.
  Preserved on rewrite, never counted as an item.
- **Un-normalized (legacy) section:** unchanged — bare lines are questions, so SPEC-0054's
  migration behaves exactly as before.

This reads as *completing* SPEC-0054 rather than reversing it: that spec already treats "already
normalized" as a meaningful state, guaranteeing idempotency on it.

## Design

- `_classify_question_lines(text)` → items carrying an optional `body`.
- `_items_to_question_body(items)` re-emits the body under its headline, so a round trip through
  any mutator is lossless.
- Every index-addressed mutator (`resolve`, `unresolve`, `edit`, `delete`,
  `set_question_priority`) counts items only — bodies are not addressable in v1.
- `normalize_idea_questions` inherits the same parser, so the corpus-wide pass stops promoting
  prose.
- **Detection rule:** a section is normalized when it contains at least one `*** OPEN|RESOLVED`
  headline and no bare line *precedes* the first headline. A file mid-migration therefore stays
  in legacy mode, which is the safe direction — it keeps migrating rather than silently
  reclassifying.

## Alternatives considered

- **Refuse the mutation loudly** — rejected: nothing is lost, but the idea becomes unusable from
  CLI *and* desk until a human edits the file, and it gives IDEA-142 nowhere to put rationale.
- **Fix only the index shift** (skip phantom items when counting) — rejected: smallest change and
  it stops the wrong-target mutation, but prose is still absorbed and IDEA-142 stays blocked.
- **Stable question ids** — rejected *for this spec*: it solves addressing permanently and would
  unblock linking rationale, but it is a much larger change to the org format and every mutator,
  and prose would still be eaten until the parser is fixed anyway. This spec does not preclude it.
- **Delete the bare-line rule** — rejected: it is SPEC-0054's migration path.

## Acceptance criteria

- [x] Prose under a question in a normalized section survives resolve / unresolve / edit /
      delete / priority and `normalize-questions`.
- [x] Indices count questions only: with prose present, `--resolve N` hits the Nth **question**.
- [x] A legacy (un-normalized) section still migrates bare lines into questions.
- [x] Indented and unindented prose behave the same in a normalized section.
- [x] `wt idea show` / `--json` report the same question count as before for files with no prose.

## Test plan

**Executed 2026-07-31.** `tests/test_question_bodies.py` — 19 tests.

- **Both IDEA-143 reproductions**, parametrised over indented *and* unindented prose: the body
  is not a question, and `--resolve 2` hits the second **question** rather than the prose.
- **Round trip:** parametrised over every index-addressed mutator — resolve, unresolve, edit,
  priority, delete, add — the body survives and never appears as `*** OPEN We decided…`; a
  three-mutation sequence leaves exactly one copy; a multi-line body keeps both lines.
- **Legacy migration intact:** bare lines still become questions; checkbox / `(resolved)` /
  bullet forms still classify; a **half-migrated** section (content before the first headline)
  is detected as *legacy*, so it keeps migrating rather than reclassifying questions as prose.
- **`normalize-questions`:** the corpus-wide invocation leaves a normalized file with a body
  **byte-identical**, and remains idempotent on legacy files.
- **Counts stay honest:** `open_questions` and `question_items` report 2, not 3, with prose
  present — so the SPEC-0110 `q` column does not inflate.

**Verified against the pre-fix parser** by forcing `normalized = False`: **11 of the 19 fail**,
including both reproductions and every mutator round trip. Restored, all 19 pass.

- **Manual verification** in an isolated `WT_CONFIG_DIR`: hand-wrote an unindented rationale
  under question 1, ran `--resolve 2`, `--edit`, `--priority` and `normalize-questions`, and
  read the file each time — body intact, `*** RESOLVED second question?` correct,
  `normalize-questions` reported "nothing to rewrite". A legacy file still migrated
  `bare one` / `bare two` into questions.
- **Regression guard:** `uv run pytest` — 970 passed; `test_questions_state.py` and
  `test_question_crud.py` green, so SPEC-0054/0101 behaviour is unchanged.

## Rollout / migration

No migration is performed. Files already damaged by this bug contain phantom questions that are
now indistinguishable from real ones — inventing a repair heuristic would risk deleting genuine
questions. The fix stops further damage; repairing existing files is a manual, human judgement
call. **Worth a follow-up idea: a `--dry-run` report of questions that look like absorbed prose.**

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — all three resolved on IDEA-143 before promotion)
