---
id: SPEC-0081
title: "Record exploration explicitly on an idea: seeded-with-context is"
status: done
owner: user
created: 2026-07-28
source_idea: IDEA-105
updated: 2026-07-28
milestone: "M4: cli ergonomics"
tags: [org, ideas, workflow, skills]
depends_on: [SPEC-0076]
# supersedes: []
# superseded_by: SPEC-NNNN
---

## Context

Promoted from idea `IDEA-105` (Record exploration explicitly on an idea: seeded-with-context is indistinguishable from explored, and repeat explorations are unrecorded).

  :PROPERTIES:
  :ID: IDEA-105
  :CREATED: [2026-07-28 Tue 07:49]
  :UPDATED: [2026-07-28 Tue 07:52]
  :PROJECT: Meta-Tools
  :KIND: improvement
  :END:
** Summary
An idea's state cannot tell you whether it has been **explored**, and nothing records that exploration happened at all — let alone how many times.

**How the ambiguity arises.** `/wt-seed` writes real explore-quality content (Summary, Open questions, Log) straight from conversation, and captures with `--state INCUBATE` because that is honest — the idea /is/ past a bare one-liner. `/wt-explore` produces the same three sections and the same state. Afterwards the two are **indistinguishable on disk**: same state, same populated sections, no marker saying which happened. Observed live in this session — [[IDEA-103]] was seeded with content carried over from [[IDEA-101]]'s exploration and looked identical to a genuinely explored idea; the human had to ask.

**The promote gate makes it worse, because it is a proxy.** `next_step_for_idea` (`src/wt/workflow.py:147-153`) recommends `wt spec new --from-idea` as soon as `idea_summary_text` is non-empty. A non-empty Summary is /evidence of writing/, not evidence of research, so a seeded-but-unexplored idea is advertised as ready to promote. [[IDEA-103]] currently reports `next: wt spec new --from-idea IDEA-103` despite no prototype, no theme check and 6 untouched questions.

**Repeat exploration is a first-class case and is also unrecorded.** Ideas get explored more than once — a second pass after new information, or a re-explore after a spec is superseded. Today the only trace is that Log entries accumulate, and Log entries are written by seeding, by `wt idea log`, and by `close` too, so they cannot be counted as explorations.

**There is direct precedent for the mechanism.** SPEC-0076 added `:CREATED:` / `:UPDATED:` as drawer properties stamped inside the write each mutator already performs (`stamp_updated` / `_inject_property` in `src/wt/org_write.py`), with a backfill command for the existing corpus. An `:EXPLORED:` marker — a count, a last-explored stamp, or both — is the same shape and can reuse that machinery rather than inventing any.

**What this would unlock beyond bookkeeping:** the promote gate could stop guessing. `wt next` could say "explore first" for a seeded-but-unexplored idea instead of recommending a spec, which is the concrete harm today.
** Open questions
*** RESOLVED What exactly is recorded — a boolean =:EXPLORED: t=, a count =:EXPLORED: 3=, a last-explored timestamp, or a count *plus* the latest stamp? Repeat exploration is explicitly in scope, so a bare boolean is probably too thin.
*** RESOLVED Should each exploration instead be a *structured Log entry* (e.g. a marked =*** [stamp] EXPLORED= headline) so the history is visible in the body rather than collapsed into a property? A property answers "how many"; a log answers "when, and what came of each".
*** RESOLVED Who writes it — the =/wt-explore= skill calling a new =wt idea explored <ID>= command, or a =wt= primitive that the skill invokes as part of its existing writes? Guidance-only failed for [[IDEA-098]]; a skill that forgets the marker recreates this exact bug.
*** RESOLVED Should ~next_step_for_idea~ change its gate from "Summary non-empty" to "has been explored"? That is the real payoff, but it changes the recommendation for every existing idea — 26 open ideas would need backfilling or would suddenly read as unexplored.
*** RESOLVED Backfill: can exploration be inferred for the existing corpus at all? Log entries are written by seed, explore, close and manual notes alike, so there may be no reliable signal — in which case existing ideas are simply unmarked, as SPEC-0076 accepted for =:CREATED:=.
*** RESOLVED Does =/wt-seed= also need to mark itself (=:SEEDED:=), so the two provenances are distinguishable rather than just "explored or not"? That is the actual question the human asked — telling seeded-with-context apart from explored.
*** RESOLVED Should the =INCUBATE= state stop being auto-set by seeding, so state alone carries the distinction? Cheaper than a property, but it makes =/wt-seed= write a less honest state and does not handle repeat explorations.
** Log
*** [2026-07-28 Tue 07:50]
Seeded from conversation. The human named the pattern after it bit them: "I ask you to seed and you seed it but jump straight into the INCUBATE state, which is not wrong because you already add much context beyond just the initial idea description. But after that, I am unsure if it has been explored or not."

Grounded at seed time:
- The promote gate is a proxy for research: `next_step_for_idea` (`src/wt/workflow.py:147-153`) recommends promotion the moment `idea_summary_text` is non-empty.
- Confirmed live: [[IDEA-103]] reports `next: wt spec new --from-idea IDEA-103` while having had **no** exploration of its own — its Summary was carried over from [[IDEA-101]]. [[IDEA-104]] and [[IDEA-101]] report the same hint despite very different amounts of actual research behind them.
- Log entries cannot serve as the signal: seeding, `wt idea log`, and `wt idea close` all append them.
- Precedent for the fix exists in SPEC-0076 (`:CREATED:`/`:UPDATED:` drawer properties stamped inside existing writes, plus a one-shot backfill), so no new machinery is needed.

Sibling to [[IDEA-098]] and [[IDEA-099]]: all three are cases of the workflow failing to **record** something it did, where the state model looked sufficient until a human noticed the gap. Nothing built.
*** [2026-07-28 Tue 07:52]
Explored `/home/user/work/tools/work-tracking` (research root, internal). Human decisions taken: **a property** (this is metadata, not narrative), and the `wt next` gate is **out of scope for now** — my judgment on that: changing the promote gate would reclassify all 26 open ideas as unexplored in one step, which is a separate decision that should be made once the data exists, not blind.

**1 — One property is enough to answer the actual question.** The confusion is "seeded-with-context vs explored". If exploration is the /only/ thing marked, then `INCUBATE` with no marker **is** the seeded-but-unexplored state, and no second `:SEEDED:` property is needed. That kills one open question outright and avoids touching `/wt-seed` at all.

**2 — Shape: a count plus a latest stamp.** Repeat exploration is explicitly in scope, so a boolean is too thin. Two drawer properties mirror SPEC-0076's naming: `:EXPLORED: <n>` (how many passes) and `:EXPLORED_AT: [YYYY-MM-DD Day HH:MM]` (the latest, using `_inactive_stamp(with_time`True)` so it matches `:CREATED:`/`:UPDATED:= and parses with `parse_inactive_stamp` from SPEC-0077).

**3 — A skill cannot be trusted to remember; it needs a primitive to call.** `/wt-explore` is a Markdown skill, and [[IDEA-098]] proved that guidance-only loses (no skill has ever mentioned `--resolve`). So the marker needs a `wt` command the skill invokes as an explicit step: `wt idea explored <ID>`. Reusing the existing machinery: `_inject_property` / `set_property` (`src/wt/org_write.py`) already write drawer properties atomically with a drift guard, and `:UPDATED:` will bump for free because `set_property` stamps ideas (SPEC-0076).

**4 — What must NOT bump it.** `wt idea log` / `summary` / `questions` are the writes an exploration /uses/, but they are also what seeding and ordinary note-taking use. If any of them incremented the counter, seeding would immediately look like an exploration and the bug would survive the fix. So the increment must be **explicit only** — exactly the inverse of SPEC-0076's `:UPDATED:`, which bumps on all of them. Worth stating loudly in the spec because it is counter-intuitive next to that precedent.

**5 — Surfacing.** Two payloads already omit-when-empty and take extra properties cleanly: `idea_show_payload` (`src/wt/explore.py:635`, which already lifts `CLOSE_REASON`/`FOLDED_INTO`/`SUPERSEDED_BY` via a tuple loop — the same loop takes these two) and `idea_row` (`src/wt/report.py:31`, where SPEC-0076 added `created`/`updated` the same way). `format_idea_show` (`:691`) prints `kind:` / `project:` / `spec:` meta lines and is the natural place for a human-readable `explored:` line.

**6 — Backfill is impossible and that is fine.** Exploration cannot be inferred: Log entries are written by seeding, by `wt idea log`, and by `wt idea close` alike, so there is no signal to mine — the same conclusion SPEC-0076 reached for `:CREATED:`. Existing ideas stay unmarked, which is honest: nobody knows whether they were explored.

**Consequence for the ideas in flight:** [[IDEA-101]] was genuinely explored, [[IDEA-103]] and [[IDEA-104]] were not (their content is carried over / conversational). After this lands, only ideas explored from here on will be marked, so those three stay indistinguishable retroactively — which is precisely the cost of not having had the property.

## Goals / Non-goals

**Goals**

- An idea records whether it has been explored, how many times, and when the latest pass was.
- The marker is written only by an explicit act, so seeding can never masquerade as exploration.
- `wt idea show` (both pretty and `--json`) and the idea row payload expose it.
- `/wt-explore` gains the step that writes it, so the skill cannot silently skip it.

**Non-goals**

- **Not changing the promote gate.** `next_step_for_idea` keeps using "Summary non-empty"
  (`src/wt/workflow.py:147-153`). Switching it to "has been explored" would reclassify all 26
  open ideas as unexplored in one step; that decision should be made once the data exists, not
  blind. Filed as the follow-up this spec makes possible.
- No `:SEEDED:` property. Marking exploration alone is sufficient — see Decision.
- No backfill. Exploration cannot be inferred for existing ideas; they stay unmarked.
- No new state. `INCUBATE` keeps its meaning; this is metadata beside it.
- Not displaying it in the `wt ideas` table. The column budget is contested (SPEC-0075/0077) and
  this is per-idea detail, not triage-scan material.

## Decision

Two drawer properties, written only by a new explicit command:

| Property | Value | Written by |
|---|---|---|
| `:EXPLORED:` | integer pass count | `wt idea mark-explored <ID>`, incrementing |
| `:EXPLORED_AT:` | `[YYYY-MM-DD Day HH:MM]` | same, overwritten each time |

`wt idea mark-explored <ID>` increments the count and refreshes the stamp. Nothing else ever touches
either property.

**One property answers the real question.** The confusion is *seeded-with-context vs explored*.
If exploration is the only thing marked, then `INCUBATE` with no `:EXPLORED:` **is** the
seeded-but-unexplored state. That needs no `:SEEDED:` property and no change to `/wt-seed` at all.

**The counter-intuitive part, stated loudly:** unlike SPEC-0076's `:UPDATED:`, which bumps on
every content and lifecycle write, `:EXPLORED:` must bump on **nothing implicit**.
`wt idea summary` / `questions` / `log` are the writes an exploration *performs*, but they are
equally the writes seeding performs. If any of them incremented the counter, seeding would
immediately look like an exploration and the bug would survive its own fix.

## Design

### `mark_explored(cfg, selector)` (`src/wt/explore.py`)

```python
def mark_explored(cfg, selector):
    """Record an exploration pass: increment :EXPLORED:, refresh :EXPLORED_AT:.
    Returns the new count."""
```

- Reads the current `:EXPLORED:` via `task.properties`, coercing a missing/garbage value to 0, so
  a hand-edited file degrades to "this is pass 1" rather than raising inside a listing command.
- Writes both properties through `set_property` (`src/wt/org_write.py:140`), which is
  line-anchored, drift-guarded and atomic. `:UPDATED:` bumps for free, since `set_property`
  stamps ideas (SPEC-0076) — correct here: recording an exploration *is* touching the idea.
- Requires the target to be an idea (`_require_idea`), like every other `explore.py` mutator.
- The stamp uses `_inactive_stamp(cfg, with_time=True)`, so `:EXPLORED_AT:` matches
  `:CREATED:`/`:UPDATED:` in format and parses with `parse_inactive_stamp` (SPEC-0077).

Two `set_property` calls means two writes. Accepted: this is an explicit, once-per-exploration
command, not a hot path — unlike SPEC-0076's stamping, which had to ride an existing write because
it fired on every mutation.

### CLI — `wt idea mark-explored <selector>`

Prints the new count (`✓ IDEA-105 explored (pass 2)`). No flags; a `--count N` override would only
invite the marker to drift from reality.

*(As-built: named `mark-explored`, not `explored`.* `wt idea explore` already exists as a **hidden
alias for `log`** (SPEC-0031, `src/wt/cli.py:334`). `explored` would have sat one letter from it,
so a mistyped command would silently append a Log entry instead of recording the pass — the exact
class of quiet-wrong-thing this spec exists to prevent. Found because
`test_cli_idea_help_mentions_capture_and_log` asserted `"explore" not in help`; that assertion was
tightened to a per-line command check rather than weakened, since a substring test would forbid
any command named after exploration.)*

### Surfacing

- `idea_show_payload` (`src/wt/explore.py:635`) already lifts `CLOSE_REASON`/`FOLDED_INTO`/
  `SUPERSEDED_BY` through a `(prop, key)` tuple loop — `EXPLORED`/`EXPLORED_AT` join it, omitted
  when absent. `explored` is emitted as an int.
- `format_idea_show` (`:691`) gains an `explored:` meta line beside `kind:`/`project:`/`spec:`,
  shown only when marked: `explored: 2 passes (latest [2026-07-28 Tue 09:14])`.
- `idea_row` (`src/wt/report.py:31`) gains `explored`, omitted when absent, exactly as SPEC-0076
  added `created`/`updated`. No table column.

### `/wt-explore` skill

A step 5 (`wt idea mark-explored <ID>` after writing findings) and a Verify line. This is the same
guidance layer that failed for IDEA-098 — which is why the marker is a *command* the skill calls
rather than a convention it is asked to remember.

## Alternatives considered

- **A structured Log entry per exploration** (`*** [stamp] EXPLORED …`) — richer, since it records
  what each pass found rather than just a count. Rejected on the human's call that this is
  metadata; also, the Log is already the narrative and would need a parser to answer "how many".
- **A boolean `:EXPLORED: t`** — too thin: repeat exploration is explicitly in scope.
- **Add `:SEEDED:` too** — makes provenance symmetric, but the seeded state is already implied by
  the absence of `:EXPLORED:`, so it is a second property that adds nothing.
- **Bump the marker from `wt idea log`** — zero friction and self-defeating: seeding writes Log
  entries, so it would immediately re-create the ambiguity.
- **Stop `/wt-seed` setting `INCUBATE`** so state alone carries the distinction — cheaper, but it
  makes seeding write a less honest state and cannot represent repeat exploration at all.
- **Change the promote gate in the same spec** — the actual payoff, deliberately deferred: it
  changes every open idea's recommendation at once and deserves its own decision.
- **Infer a backfill from Log entries** — impossible; seeding, `wt idea log` and `wt idea close`
  all write them.

## Acceptance criteria

- [x] `wt idea mark-explored <ID>` on an unmarked idea sets `:EXPLORED: 1` and an
      `:EXPLORED_AT:` stamp.
- [x] Running it again sets `:EXPLORED: 2` and refreshes `:EXPLORED_AT:`; the count keeps rising.
- [x] A garbage or missing `:EXPLORED:` value is treated as 0, not an error.
- [x] `wt idea summary`, `wt idea questions` (set/add/resolve), `wt idea log`, `wt idea retitle`,
      `wt idea kind`, `wt state`, `wt idea clock-in`/`clock-out` and capture leave both properties
      untouched.
- [x] `wt idea mark-explored` bumps `:UPDATED:` (it is a real touch) but never `:CREATED:`.
- [x] A freshly seeded idea has no `:EXPLORED:`, so `INCUBATE` + absent marker is distinguishable
      from an explored idea.
- [x] `wt idea show --json` includes `explored` (int) and `explored_at` when marked, omits both
      when not; existing keys unchanged.
- [x] `wt idea show` (pretty) prints an `explored:` line when marked and nothing when not.
- [x] `idea_row` includes `explored` when marked; `wt ideas --json` rows keep their existing keys.
- [x] `wt ideas` / `wt next` tables are unchanged (no new column).
- [x] `next_step_for_idea` output is unchanged for every existing idea.
- [x] `skills/wt-explore/SKILL.md` documents `wt idea mark-explored`, in both procedure and Verify.
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_explored_marker.py` (27 tests):

- `test_first_pass_sets_count_and_stamp` / `test_repeat_pass_increments`.
- `test_garbage_count_coerces_to_zero` — hand-write `:EXPLORED: banana`; next call yields 1.
- `test_nothing_else_bumps_explored` — parametrised over capture, summary, questions
  (set/add/resolve), log, retitle, kind, state, clock-in/out: both properties byte-identical.
  This is the test that keeps the fix from defeating itself, so it is enumerated per mutator.
- `test_explored_bumps_updated_not_created` — the SPEC-0076 interaction.
- `test_seeded_idea_is_distinguishable` — an `INCUBATE` idea with Summary but no marker reads as
  unexplored; after one call it reads as explored. The actual bug, asserted directly.
- `test_show_payload_and_pretty_output` — `explored`/`explored_at` present when marked, absent
  when not; the pretty printer shows a line only when marked.
- `test_idea_row_exposes_explored`.
- `test_tables_unchanged` — `wt ideas` / `wt next` headers have no `explored` column.
- `test_next_step_unchanged` — the hint for a marked and an unmarked idea is identical (the gate
  is explicitly not changing).
- `test_skill_documents_explored` — meta-test on `skills/wt-explore/SKILL.md`; doc drift is the
  failure mode this family of bugs keeps hitting.

**Manual verification**

1. `uv run wt idea mark-explored IDEA-101` (genuinely explored earlier) then
   `wt idea show IDEA-101` → `explored: 1 pass (latest [2026-07-28 Tue 07:57])`. **Done.**
2. `uv run wt idea show IDEA-103` → no `explored:` line, because it was seeded from
   IDEA-101's findings rather than explored. **Done** — that pair is the whole point of the spec,
   and it is now readable at a glance.
3. `uv run wt ideas` — header still `id state kind project updated idea`, no new column. **Done.**

**Regression guard**

Full `uv run pytest`; `tests/test_idea_stamps.py` (SPEC-0076's bump matrix) and
`tests/test_idea_freshness.py` must pass untouched, and `tests/test_json_cli.py` covers the
envelopes.

## Clock Log

Clocked on IDEA-105 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

No migration; existing ideas stay unmarked, which is honest — nobody knows whether they were
explored. Marking accrues from the next exploration onward. The `/wt-explore` skill change ships
in the same commit so tooling and guidance arrive together.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Property vs Log entry* → property (human's call: this is metadata).
- *Shape* → count plus latest stamp; a boolean cannot express repeat passes.
- *Who writes it* → an explicit `wt idea explored` command the skill calls; guidance alone failed
  for IDEA-098.
- *Also mark seeding* → unnecessary; absence of `:EXPLORED:` is the seeded state.
- *Promote gate* → unchanged here, deliberately.
- *Backfill* → impossible; existing ideas stay unmarked.
