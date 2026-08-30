---
id: SPEC-0080
title: "Promotion never resolves the source idea's Open questions:"
status: done
owner: user
created: 2026-07-27
source_idea: IDEA-098
updated: 2026-07-27
milestone: "M4: cli ergonomics"
tags: [cli, ideas, workflow, skills]
depends_on: [SPEC-0054, SPEC-0078]
# supersedes: []
# superseded_by: SPEC-NNNN
---

## Context

Promoted from idea `IDEA-098` (Promotion never resolves the source idea's Open questions: wt-new-work leaves them OPEN after the spec decides them, and no skill ever calls wt idea questions --resolve).

  :PROPERTIES:
  :ID: IDEA-098
  :PROJECT: Meta-Tools
  :KIND: bug
  :UPDATED: [2026-07-27 Mon 21:21]
  :END:
  :LOGBOOK:
  CLOCK: [2026-07-27 Mon 21:20]
  :END:
** Summary
Observed live while promoting [[IDEA-092]] → SPEC-0075. The spec explicitly **decided all five** of the ideas Open questions (each one is answered in its `## Open questions` section, which reads "None — resolved during authxxing"), yet all five headlines on the idea were still `*** OPEN` afterwards. The human caught it, not the workflow.

**The bug is guidance, not code.** The primitive already exists: `wt idea questions <sel> --resolve N` flips the Nth headline to `RESOLVED` (SPEC-0054, `resolve_question` `src/wt/explore.py:295`). Nothing calls it.

Verified across the repo-owned skills (`skills/`, the source of truth that `wt skills` installs):
- **No skill mentions `--resolve` at all.** `grep -rln "--resolve" skills/` → zero hits.
- Questions are only ever **written**: `wt-explore` (`skills/wt-explore/SKILL.md:31`) and `wt-seed` (`:27`) both document `--set` / `--add` for raising questions.
- `wt-new-work/SKILL.md` never mentions questions **at all** — not in its procedure, its guardrails, or its Verify block. Its Verify only checks spec lint, `status: accepted`, ledger currency, and no template placeholders.

So the `RESOLVED` half of SPEC-0054 is **write-only in practice**: the state exists in the data model and the CLI, and no documented workflow ever reaches it. Every idea promoted so far likely carries stale OPEN questions that its spec already answered — the question list rots into a false to-do list, which is worse than empty because it looks authxxitative.

**The asymmetry that makes this bite:** `docs/specs/SCHEMA.md` requires a /specs/ Open questions to be empty before `accepted`, and lint pressure keeps that true. There is no equivalent pressure on the /idea/ side, so promotion silently drops the correspondence between "question the idea raised" and "decision the spec made".

**Shape of the fix** (design deliberately left open):
- At minimum, a step + Verify line in `skills/wt-new-work/SKILL.md`: after the spec is accepted, resolve every source-idea question the spec decided, and say which spec section decided it.
- Possibly stronger: have `wt spec new` / promotion warn when the source idea has OPEN questions, or an advisory lint like `check_source_idea_promotion` (`tools/spec_lint.py:177`) that flags an `accepted`/`done` spec whose `source_idea` still has OPEN questions. That check is the closest existing precedent — it already flags a spec whose idea never left the pre-promotion states, so the pattern for "spec and idea drifted apart" is established.
- Also worth deciding: is bulk resolution wanted (`--resolve-all`), since resolving five questions today took five separate invocations?
** Open questions
*** OPEN Enforcement or guidance? A =skills/wt-new-work/SKILL.md= step is the cheap fix, but guidance is exactly what already failed here — an advisory lint (sibling of ~check_source_idea_promotion~, =tools/spec_lint.py:177=) would catch it mechanically. Both?
*** RESOLVED Should ~wt spec new~ warn at promotion time when the source idea has OPEN questions, or is promotion too early — the spec has not been authxxed yet, so the questions are legitimately still open at that moment? (If so, the right gate is at ~accepted~, not at ~new~.)
*** RESOLVED Add ~--resolve-all~ / multi-index resolve? Resolving IDEA-092s five questions took five separate CLI invocations.
*** RESOLVED Is "resolved by promotion" distinct from "resolved by research"? A question the spec *decided* differs from one explore *answered* — worth recording /which spec/ resolved it (a ~:RESOLVED_BY:~ note or a Log line), or is a bare =RESOLVED= flip enough?
*** OPEN What about questions the spec deliberately did *not* answer — e.g. deferred to another idea or declared a non-goal? Those should probably not be flipped to =RESOLVED=; is a third state needed (=DEFERRED=/=MOOT=), or does a Log note cover it?
*** RESOLVED Backfill: how many already-promoted ideas carry stale OPEN questions their specs already decided? Needs a survey before deciding whether a one-shot cleanup is warranted.
*** OPEN Do the sibling skills need the same treatment — =wt-rework= (supersede/extend) and =wt-implement-spec= can also resolve open questions as a side effect of doing the work.
** Log
*** [2026-07-27 Mon 18:34]
Found by the human during the [[IDEA-092]] → SPEC-0075 promotion, immediately after the spec was accepted: "why do the questions remain OPEN in the org file? This feels like a failure of our workflow internal guidance." Correct diagnosis — it is guidance, not a missing primitive.

Evidence gathered in `/home/user/work/tools/work-tracking` (research root, internal):
- `resolve_question` exists (`src/wt/explore.py:295`), exposed as `wt idea questions <sel> --resolve N` (SPEC-0054). It works — used it to flip all five IDEA-092 questions to `RESOLVED` after the fact.
- `grep -rln "--resolve" skills/` → **zero hits**. No repo-owned skill documents the resolve half of the lifecycle.
- `skills/wt-new-work/SKILL.md` does not mention questions anywhere: not in the procedure, guardrails, or Verify.
- Question-writing guidance exists in `wt-explore` (`:31`) and `wt-seed` (`:27`) — so the asymmetry is raise-only.
- Closest existing precedent for a mechanical check: `check_source_idea_promotion` (`tools/spec_lint.py:177`), an advisory (not pytest-gated) check that flags a `done` spec whose `source_idea` never left `IDEA`/`INCUBATE`/`SPECCED`. Same class of problem: spec and idea drifting apart after promotion.

Immediate remediation already applied to IDEA-092 (all five questions flipped to `RESOLVED`); this idea covers the systemic fix so it stops recurring.

Note the contrast that makes this a real defect rather than a nit: `docs/specs/SCHEMA.md` says a /specs/ Open questions must be empty before `accepted`, and lint keeps that honest. The /idea/ side has no equivalent pressure, so the raise→decide correspondence is silently lost on every promotion.
*** [2026-07-27 Mon 21:20]
Explored `/home/user/work/tools/work-tracking` (research root, internal). The measurement, and one structural finding that decides the design.

**1 — The drift is real and quantified.** Walking every idea with a `:SPEC:` in a terminal state (`PROMOTED`/`EXPORTED`): **26 ideas carry ~75 open questions** after their spec landed. Worst offenders: IDEA-012, IDEA-017, IDEA-018 (5 each); IDEA-048/049/050/051/046 (4-5 each, all exported PFW-Intelligence work). So the prediction made at capture time holds, with a number on it.

**2 — Resolution is NOT derivable. This is the key difference from [[IDEA-099]]/SPEC-0078.** That bug was fixable by a command because idea /state/ is a pure function of the spec's `status`. Nothing can mechanically decide whether a spec answered a given question — it needs a human (or an authxxing agent) to read both. Sampling confirms a genuine mix rather than uniform staleness:
- `IDEA-012` (wt-seed): all 5 open questions read as **decided** — the skill shipped, so "skill-only vs thin CLI helper" and "preview vs fire-and-forget" were settled by what was built.
- `IDEA-017`: already **mixed** — 2 `RESOLVED`, 5 `OPEN`, and several of the open ones (manifest expressiveness, target wiring, ownership of template drift) look genuinely unsettled, not stale.
So a bulk auto-resolve would be **wrong**, and any design premised on "reconcile can close them like it closes state" is unbuildable. The fix can only **surface** the drift and make closing it cheap.

**3 — Closing them is currently tedious enough to discourage it.** `resolve_question` (`src/wt/explore.py:295`) takes a single 1-based index; the CLI exposes `--resolve INTEGER` (one per invocation). Resolving IDEA-092's five questions took five separate commands, and IDEA-099's nine took nine. That friction is part of why the backlog grew.

**4 — The state vocabulary is binary, which blocks one otherwise-attractive option.** `*** OPEN|RESOLVED` is baked into `_QHEAD_RE` (`explore.py:31`), with the historical labels folded into those two by `_QLABEL_MAP` (`:38-44`; `LOCKED`→resolved, `OPTIONAL`→open+[#C]). A question the spec deliberately **declined** to answer (deferred to another idea, or declared a non-goal) has nowhere honest to go: marking it `RESOLVED` is a lie, leaving it `OPEN` is the drift. Adding a third state touches the regex, the label map, the classifier, the CLI and every existing file — real work, and separable.

**5 — There is a natural home for the surfacing.** `reconcile_ideas` (`src/wt/specs.py`, SPEC-0078) already walks exactly the right population — every `:SPEC:`-linked idea, resolving internal and outbound alike — and already reports per-idea rows. Adding a "spec done but N questions still open" row is the same walk, no new traversal, and it lands in a command that is already run.

**Shape this points to** (small, cohesive): surface the drift in `reconcile`; make `--resolve` accept several indices (or all) so closing is one command; add the missing step + Verify line to `skills/wt-new-work/SKILL.md`. Defer the third state, exactly as SPEC-0078 deferred `SHIPPED`.

## Goals / Non-goals

**Goals**

- Questions left open on an idea whose spec has landed are *visible*, in a command already run.
- Closing them is one invocation, not one per question.
- The promote workflow tells the authxx to close them, and its Verify step checks.

**Non-goals**

- **No automatic resolution.** Whether a spec answered a question is not derivable; see Decision.
- Not adding a third question state (`DEFERRED`/`MOOT`) for questions a spec deliberately
  declined to answer. It is the honest modelling fix but touches the headline regex, the label
  map, the classifier, the CLI and every existing file — separable, and filed on its own.
- Not bulk-resolving the existing 75. They are a genuine mix of decided and still-open; the tool
  surfaces them, a human closes them.
- No change to the question file format or to `wt.idea.v1`.

## Decision

Three small pieces, no cleverness:

1. **Surface.** `wt spec reconcile` gains a `questions-open` row: *spec is `done` but the idea
   still has N open questions*. Report-only — never written, in either mode, including `--apply`.
2. **Ergonomics.** `wt idea questions <sel> --resolve` accepts multiple indices
   (`--resolve 1 --resolve 3`) and `--resolve-all`.
3. **Guidance.** `skills/wt-new-work/SKILL.md` gains a step after acceptance ("resolve every
   source-idea question the spec decided, and say which section decided it") and a Verify line.

The load-bearing question this idea raised was *guidance or enforcement*. The answer is both,
weighted to enforcement: guidance alone is exactly what failed here — the skill has never
mentioned `--resolve` — so the mechanical surfacing in (1) is the part that has to carry it, and
(3) is a complement.

### Why nothing resolves automatically

SPEC-0078 could reconcile *state* because state is a pure function of the spec's `status`.
Question resolution is not: deciding whether a spec answered a given question requires reading
both. Sampling the real backlog shows the mix is genuine, not uniform staleness — `IDEA-012`'s
five open questions were all settled by what shipped, while `IDEA-017` has two `RESOLVED`
alongside open ones (manifest expressiveness, target wiring) that are still genuinely unsettled.
An auto-resolve would silently close live design questions. So the tool's job ends at making the
drift impossible to miss.

## Design

### Surfacing (`src/wt/specs.py`)

`reconcile_ideas` already walks every `:SPEC:`-linked idea and loads its spec's frontmatter, so
this is one extra check in the existing loop — no second traversal:

```python
if status in _DONE and (n := _open_question_count(cfg, task)):
    plan.append((idea_id, spec_id, "questions-open",
                 f"spec is done but {n} question(s) still open"))
```

`_open_question_count` reuses `explore.read_idea_questions` (`src/wt/explore.py:259`), which
already parses the `*** OPEN|RESOLVED` headlines, so there is one parser.

The row is **never acted on by `--apply`** — it is added to the report only. The write pass
already iterates its own `advances`/`backlinks` lists rather than the plan, so this is
structurally guaranteed rather than a matter of remembering an `if`.

The count also joins `stale_idea_count`'s siblings as `open_question_count`, surfaced on
`wt hub --json` as `ideas_with_open_questions`. `wt next` keeps a single drift line; adding a
second would turn the panel into a noticeboard.

### Multi-resolve (`src/wt/explore.py`, `src/wt/cli.py`)

`resolve_question(cfg, selector, index)` gains a sibling
`resolve_questions(cfg, selector, indices=None)`:

- `indices=None` resolves every currently-open question.
- Indices are validated **as a set, before any write** — a partially-applied bulk resolve is
  worse than a rejected one.
- Resolution happens in a single `_replace_section_body` call, so it is one file write and one
  `:UPDATED:` bump (SPEC-0076) regardless of how many questions close.
- Already-resolved indices are accepted as no-ops, so `--resolve-all` is idempotent.

CLI: `--resolve` becomes `multiple=True`, plus `--resolve-all`. Passing both is an error.

### Skill (`skills/wt-new-work/SKILL.md`)

New step 6 (before epic children), and a Verify line: `wt idea show <id>` shows no `OPEN`
question the spec decided. Mirrors how `wt-export` documents the `EXPORTED` advance.

## Alternatives considered

- **Auto-resolve every question when the spec reaches `done`** — the obvious symmetry with
  SPEC-0078, and wrong: it would close genuinely-open design questions. Rejected on evidence
  from the real backlog, not on principle.
- **Block acceptance while the source idea has open questions** — enforceable and strict, but
  wrong-headed: at authxxing time the questions *should* still be open; they are what the spec is
  about to decide. The gate belongs after `done`, which is where the surfacing sits.
- **A lint check like `check_source_idea_promotion`** — it would work, but that check is opt-in
  and wired to nothing, which is precisely how 26 ideas accumulated. Putting it in `reconcile`
  means it appears in a command with a reason to be run.
- **Add a `DEFERRED` state now** — the honest fix for "the spec declined to answer this", and a
  vocabulary migration. Deferred like SPEC-0078 deferred `SHIPPED`.
- **Bulk-resolve the existing 75 as part of rollout** — rejected: they are mixed, and closing a
  live question is unrecoverable without reading the file.

## Acceptance criteria

- [x] `wt spec reconcile` reports `questions-open` for an idea whose spec is `done` and which has
      at least one open question.
- [x] It does not report it when the spec is not `done`, or when no question is open.
- [x] `--apply` never changes a question's state — the file is byte-identical apart from any
      state advance it was already going to make.
- [x] `wt idea questions <id> --resolve 1 --resolve 3` resolves both and leaves the others open.
- [x] `wt idea questions <id> --resolve-all` resolves every open question and is idempotent.
- [x] An out-of-range index in a multi-resolve rejects the whole call and writes nothing.
- [x] A bulk resolve of N questions performs exactly one file write.
- [x] `--resolve` together with `--resolve-all` is an error.
- [x] `wt hub --json` exposes `ideas_with_open_questions`; existing keys unchanged.
- [x] `skills/wt-new-work/SKILL.md` documents resolving source-idea questions, in both its
      procedure and its Verify block.
- [x] Running reconcile against the real corpus reports the affected ideas. *(As-built: **18**,
      not the 26 quoted at capture. The 26 counted every terminal idea with open questions; 8 of
      those link to a spec that has not reached `done`, where an open question is correct rather
      than stale. The narrower number is the right one — it is the population this spec claims
      is drifting.)*
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — extend `tests/test_reconcile.py`, and `tests/test_questions_state.py` for
the resolve API:

- `test_questions_open_reported_when_spec_done` / `test_not_reported_when_spec_not_done` /
  `test_not_reported_when_no_open_questions`.
- `test_apply_never_touches_questions` — questions byte-identical after `--apply` on an idea that
  also gets a state advance. Guards the one thing this spec must not do.
- `test_resolve_multiple_indices` — 1 and 3 resolved, 2 left open.
- `test_resolve_all` and `test_resolve_all_is_idempotent`.
- `test_bad_index_rejects_whole_call` — file byte-identical after a call mixing a valid and an
  invalid index. Partial application is the failure mode worth pinning.
- `test_bulk_resolve_is_one_write` — counts `_atomic_backup_write` calls (not backup files;
  their names collide within a second, per SPEC-0076).
- `test_resolve_and_resolve_all_conflict` — CLI error.
- `test_skill_documents_resolve` — assert `skills/wt-new-work/SKILL.md` mentions `--resolve`. A
  meta-test, because doc drift is the original defect here.

**Manual verification**

1. `uv run wt spec reconcile` — 18 ideas appear as `questions-open`. **Done.**
2. `uv run wt idea questions IDEA-012 --resolve-all` — "5 question(s) resolved"; re-running
   reconcile no longer lists it; a second `--resolve-all` reports nothing to resolve. **Done.**
   (IDEA-012 was chosen because all five of its questions were settled by the `wt-seed` skill
   that shipped — the sampled example from the exploration.)
3. `uv run wt hub --json` — `ideas_with_open_questions: 17` after step 2, `stale_ideas: 0`.
   **Done.**

**Regression guard**

Full `uv run pytest`; `tests/test_questions_state.py` (the SPEC-0054 model) and
`tests/test_reconcile.py` (SPEC-0078 rows) must pass with their existing assertions intact.

## Clock Log

Clocked on IDEA-098 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

No data migration. The 26 ideas keep their questions until a human closes them; the point is that
they are now listed. Skill change ships in the same commit so the guidance and the tooling arrive
together.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Guidance or enforcement* → both, weighted to the mechanical surfacing; guidance alone is what
  already failed.
- *Auto-resolve on `done`* → never; resolution is not derivable.
- *Bulk resolve* → yes, `--resolve` repeatable plus `--resolve-all`, one write, all-or-nothing.
- *Third state for declined questions* → deferred to its own change.
- *Backfill the existing 75* → no; surface them, let a human close them.
