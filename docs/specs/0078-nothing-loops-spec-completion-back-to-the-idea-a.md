---
id: SPEC-0078
title: "Nothing loops spec completion back to the idea: a hand-implemented"
status: done
owner: user
created: 2026-07-27
source_idea: IDEA-099
updated: 2026-07-27
milestone: "M4: cli ergonomics"
tags: [cli, ideas, specs, workflow]
depends_on: [SPEC-0067]
# supersedes: []
# superseded_by: SPEC-NNNN
---

## Context

Promoted from idea `IDEA-099` (Nothing loops spec completion back to the idea: a hand-implemented done spec leaves its source_idea SPECCED forever, and the check that detects it is opt-in and wired to nothing).

  :PROPERTIES:
  :ID: IDEA-099
  :CREATED: [2026-07-27 Mon 19:50]
  :UPDATED: [2026-07-27 Mon 20:18]
  :PROJECT: Meta-Tools
  :KIND: bug
  :END:
** Summary
The idea→spec→done loop only closes in **one** direction, and only for outbound work. Nothing reads a finished spec back onto the idea that spawned it, so a hand-implemented internal spec leaves its idea stuck at `SPECCED` forever.

**Evidence (measured, `/home/user/work/tools/work-tracking`):** `uv run python tools/spec_lint.py --check-source-ideas` reports **13 stale source ideas** — every one a `status: done` spec whose `source_idea` never left `IDEA`/`INCUBATE`/`SPECCED`. 11 of them predate the current session (SPEC-0064…0074), so this is long-standing, not a one-off slip.

**Why it happens.** `PROMOTED` is only ever set as a side-effect of `wt spec generate` (`src/wt/specs.py::generate_from_spec`). A spec implemented by hand — the normal path when the work is a code change rather than a task breakdown — never calls generate, so nothing advances the idea. There is no hook on "spec reached `done`" at all.

**Why nothing catches it.** `check_source_idea_promotion` (`tools/spec_lint.py:177`) detects exactly this, and is **deliberately excluded** from `validate()` (it reads the machine-local `org_ideas_file`, so it must not gate `uv run pytest`). But it is wired to **nothing else** either: `grep` finds it invoked only behind its own opt-in flag `--check-source-ideas`. Reaching it requires already suspecting the problem.

**Why guidance does not save it.** The Definition of Done in `AGENTS.md` has six items (AC, test plan, no regressions, spec body, LEDGER, spec_lint) and **none** mentions the source idea. No skill covers it either: `wt-orient` documents the happy path as "internal: generate → PROMOTED", i.e. the only advancing path is generate; `wt-export` documents the outbound analogue (`EXPORTED`).

──────── The asked-for shape: a retroactive reconcile command ────────
The tracked provenance already exists for exactly this purpose — that is the point of keeping repository + spec locations:
- **Outbound** ideas carry `:TARGET_REPO:` and `:TARGET_SPEC_PATH:` (SPEC-0065/0066), and are **already** reconciled: `wt spec sweep` (SPEC-0067) walks every pending `EXPORTED` idea, mirrors the target repo status via `pull_status` (`src/wt/export.py:209`), and on the `done` transition auto-archives the idea (`export.py:236-244`).
- **Internal** ideas carry `:SPEC: SPEC-NNNN`, resolvable to `docs/specs/NNNN-*.md` in this repo (and `research.root` gives the repo location, SPEC-0042). Every ingredient is present; nothing reads it.

So the fix is the **internal mirror of** `wt spec sweep`: walk ideas with a `:SPEC:`, read that specs frontmatter `status`, and advance the idea to match — retroactively clearing the existing 11, and keeping future ones honest. `pull_status` is the model to follow, including its "only act on the transition" guard so the command stays idempotent.
** Open questions
*** OPEN Which spec statuses map to which idea states? =done= → =PROMOTED= is the obvious one, but should =in-progress= advance a =SPECCED= idea at all, and should =superseded= / =rejected= map to =DROPPED= or be left alone for a human?
*** OPEN Should the command also walk *backwards* — an idea marked =PROMOTED= whose spec is only =accepted= is also drift, just in the other direction. Reconcile both ways, or only advance?
*** OPEN Does it live as ~wt spec sweep --internal~ (one sweep, two provenance kinds) or a separate ~wt spec reconcile~? The outbound sweep is keyed on state =EXPORTED=; the internal one keys on =:SPEC:= presence, so the selection logic differs even though the intent is identical.
*** OPEN Should it be dry-run by default? Advancing to =PROMOTED= triggers auto-archival (SPEC-0073), which moves the subtree out of =ideas.org= — a bulk run over the 11 stale ideas is a big, mostly-irreversible data move to trigger without a preview.
*** OPEN Does the reconcile also want to close the loop the other way, writing the specs =source_idea= when it is missing? SPEC-0077 was hand-authxxed with no =source_idea= and was therefore invisible to ~check_source_idea_promotion~ until it was added by hand — a spec with no back-link cannot be reconciled at all.
*** OPEN Should ~check_source_idea_promotion~ become non-optional somewhere it can actually run — a pre-commit hook, or a warning line on =wt hub= / =wt next= — given that being opt-in is why 11 accumulated silently?
*** OPEN Is =PROMOTED= even the right terminal state for a hand-implemented spec? Its name and its ~wt spec generate~ origin both imply "tasks were generated"; a code-change spec that shipped may deserve a distinct state (=DONE=/=SHIPPED=) rather than borrowing this one.
*** OPEN Given the drift is already fully derivable (next_step_for_idea computes =wt tasks= for all 11 today), should reconcile be a *command* at all, or should the idea state simply stop being authxxitative — i.e. derive-on-read everywhere and treat =:SPEC:= + spec status as the single source of truth?
*** OPEN Since advancing to =PROMOTED= makes ~next_step_for_idea~ short-circuit before reading the spec (=workflow.py:174=), a wrong bulk advance is not self-correcting. Does that mean reconcile must be dry-run by default, or that =PROMOTED= should stop short-circuiting?
** Log
*** [2026-07-27 Mon 19:52]
Found by the human mid-session: "something is not looping back the spec implementation state. look at the list of ideas, for example 94/92 did not close." Correct — and the follow-up framed the fix: "we should have a command that updates all the existing ideas after the fact. that is why we keep track of repository location and spec location."

Investigated `/home/user/work/tools/work-tracking` (research root, internal):
- `check_source_idea_promotion` (`tools/spec_lint.py:177`) already detects the drift and reported **13** stale ideas; it is excluded from `validate()` on purpose (reads machine-local org) and is invoked nowhere but its own `--check-source-ideas` flag.
- `PROMOTED` is set only by `generate_from_spec` (`src/wt/specs.py`); no hook exists for "spec reached `done`".
- The outbound half is already built and is the template: `wt spec sweep` (`src/wt/export.py:395`) → `pull_status` (`:209`) mirrors the target status and auto-archives on the `done` transition (`:236-244`), keyed on `:TARGET_REPO:` / `:TARGET_SPEC_PATH:`.
- Internal ideas carry `:SPEC:`, and internal specs live at `docs/specs/NNNN-*.md`, so the same reconcile is possible with no new stored data.
- `AGENTS.md` Definition of Done has no source-idea item; no skill mentions advancing the idea after a hand-implemented spec.

Immediate remediation applied (not the fix, just the data): `IDEA-092` and `IDEA-094` advanced to `PROMOTED` (both auto-archived per SPEC-0073), and `source_idea: IDEA-092` added to SPEC-0077, which had been hand-authxxed with no back-link and was therefore invisible to the check. **11 stale ideas remain** (SPEC-0064…0074 → IDEA-064, 077-086) and were deliberately left alone: a bulk state change plus archival of 11 subtrees is the humans call, and is precisely what the asked-for command should do with a preview.

Sibling of [[IDEA-098]] (promotion never resolves the source ideas Open questions) — same root shape: the idea→spec transition is well covered, the spec→idea return path is not.
*** [2026-07-27 Mon 20:18]
Explored the implementation surface (`/home/user/work/tools/work-tracking`). Two findings collapse most of the perceived work.

**1 — The truth is already derived on every run; it is just never written down.**
`next_step_for_idea` (`src/wt/workflow.py:123`) already resolves an ideas `:SPEC:` to a path, reads the frontmatter `status`, and branches on it. For an internal spec at `status: done` it returns `"wt tasks"` (`workflow.py:197-198`). Confirmed against the live corpus: all 11 stale ideas report `next: "wt tasks"` right now, i.e. the system **knows** their specs are finished and is already handing out the post-completion hint — while their org state still says `SPECCED`. Nothing is missing from the derivation; the only missing thing is a writer.

**2 — Resolution is already provenance-agnostic.**
`_resolve_spec_path` (`workflow.py:34`) and `_load_spec_fm` (`:48`) resolve **both** kinds: outbound ids glob `outbox_dir/**/ID-**.md`, internal ids go through `_find_spec(_specs_dir(cfg), ...)`; `_is_outbound_id` discriminates. So a reconcile does not need new lookup code or new stored data for the internal case — the `:SPEC:` property plus the existing resolver is enough. This is direct support for **one** command handling both provenance kinds rather than a separate internal-only one (leaning, not decided — see the open question).

**Status vocabulary that a mapping must respect** (`workflow.py:20-22`): `_AUthxx ` {draft, proposed}`, `_READY ` {accepted, in-progress}`, `_DONE ` {done}`. Note `superseded` and `rejected` are in **none** of these — they fall through to `"review {spec} ({status})"=. So the codebase has no existing opinion on what they mean for an idea, which argues for leaving them to a human rather than inventing a mapping.

**Consequence worth weighing before choosing the terminal state:** `next_step_for_idea` treats `PROMOTED` as a hard short-circuit — it returns `"wt tasks"` before even looking at the spec (`workflow.py:174-175`), and again when the spec is missing or unreadable (`:157-158`, `:165-166`). So advancing an idea to `PROMOTED` permanently stops the hint layer from reading its spec again. That is fine for genuinely finished work, but it means a wrong bulk advance is not self-correcting — the system will never re-derive the real status afterwards. Strengthens the case for dry-run-by-default.

**Not investigated yet:** whether the 11 stale ideas Summary/Log content is still worth keeping in `ideas.org` vs archived (advancing to `PROMOTED` auto-archives via SPEC-0073), and whether `wt hub` should surface the drift.

## Goals / Non-goals

**Goals**

- One command reports every idea whose org state disagrees with its linked spec's `status`, and
  writes the fix on request.
- Works for internal (`SPEC-NNNN`) and outbound (`PROJ-NNNN`) links alike, reusing the existing
  provenance-agnostic resolver.
- Clears the 11 pre-existing stale ideas in one pass.
- Makes future drift visible where it will actually be seen, not behind an opt-in flag.
- Never destroys a human decision: forward-only writes, everything else reported.

**Non-goals**

- No new idea states. `PROMOTED` keeps doubling as "tasks generated" and "spec shipped"; naming
  that properly is its own change.
- Not rewinding an idea that is ahead of its spec (reported, never written).
- Not touching `wt spec sweep`'s outbound pull semantics — reconcile reads, sweep pulls.
- No git hook: `check_source_idea_promotion` reads a machine-local org file and would break on
  a checkout without one.
- Not replacing state with derive-on-read. Org state stays authxxitative so `ideas.org` remains
  readable on its own and the archival hooks keep firing.

## Decision

Add **`wt spec reconcile`**, dry-run by default, `--apply` to write. It walks every idea
carrying a `:SPEC:`, loads that spec's frontmatter, and compares the idea's state to what the
spec implies:

| Spec status | Idea state now | Action |
|---|---|---|
| `done` | pre-terminal (`IDEA`/`INCUBATE`/`SPECCED`) | → `PROMOTED` |
| `superseded` | pre-terminal | → `DROPPED` |
| `rejected` | pre-terminal | → `DROPPED` |
| `accepted` / `in-progress` | `IDEA`/`INCUBATE` | → `SPECCED` (left behind) |
| `accepted` / `in-progress` | `SPECCED` | no change |
| `draft` / `proposed` | any pre-terminal | no change |
| anything | already terminal, further along than the spec | **flag, never write** |

*(As-built correction.)* "Further along than the spec" originally meant *any* non-`done` status
under a terminal idea. The first dry run against the real corpus flagged 6 outbound ideas that
way — all false positives, because `EXPORTED` alongside an `accepted` outbox spec is the
*normal* state (export advances the idea while the status lags until pulled, SPEC-0041), and
`PROMOTED` alongside `accepted` is normal too (`wt spec generate` runs off an accepted spec). So
`_TERMINAL_OK` includes `accepted`/`in-progress`: only a still-being-written spec
(`draft`/`proposed`) under a terminal idea is genuine drift. Without this the command would cry
wolf on every outbound idea.

It also writes a missing `source_idea` onto a spec when the idea's `:SPEC:` points at it, since
a spec with no back-link is invisible to `check_source_idea_promotion` and unreconcilable.

Separately, the stale count is surfaced on `wt next` and in `wt hub`, so the drift stops
depending on someone remembering `--check-source-ideas`.

## Design

### Why a command and not derive-on-read

The drift is already fully derivable — `next_step_for_idea` (`src/wt/workflow.py:123`) resolves
each idea's `:SPEC:`, reads the status, and returns `wt tasks` for a `done` internal spec. All 11
stale ideas report exactly that today, while their org state says `SPECCED`. So the derivation
exists; only a writer is missing. Keeping state authxxitative (rather than computing it on read)
preserves two things: `ideas.org` still describes itself to Emacs/grep without wt, and the
archival hooks keyed on state transitions (SPEC-0073) keep working.

### `reconcile_ideas(cfg)` (`src/wt/specs.py`)

Returns `[(idea_id, spec_id, action, detail)]` with `action` in
`advance` / `flag-ahead` / `flag-no-backlink` / `unchanged` / `missing`.

- Enumerates ideas via `load_tasks` + `filter_tasks(is_idea=True)`, so rotated and archived
  files are covered (SPEC-0074), then keeps those with a non-empty `:SPEC:`.
- Resolves the spec with `workflow._load_spec_fm` (`src/wt/workflow.py:48`), which already
  handles both internal (`_find_spec(_specs_dir(cfg), …)`) and outbound
  (`outbox_dir/*/ID-*.md`) — no new lookup code, no new stored data.
- An unresolvable `:SPEC:` yields `missing` and the walk continues; one bad link must not abort
  the run, matching `sweep`'s behaviour (`src/wt/export.py:409`).
- Status vocabulary reuses `workflow._AUthxx` / `_READY` / `_DONE` rather than re-listing
  strings, plus explicit `superseded` / `rejected` handling those sets deliberately omit.
- Writes only under `apply=True`, via `set_state_by_selector`, which re-resolves per write —
  necessary because each write can shift line numbers and can archive the subtree to another
  file.
- Terminal-vs-spec mismatches (`EXPORTED`/`PROMOTED`/`DROPPED`/`RESEARCHED` where the spec is
  behind) are only ever reported. Rewinding would undo a deliberate human state, and
  `next_step_for_idea` short-circuits on `PROMOTED` before reading the spec
  (`src/wt/workflow.py:174`), so a wrong write is not self-correcting.

### `--apply` and archival

`PROMOTED` and `DROPPED` are both in `_ARCHIVE_ON_STATES`, so applying moves those subtrees into
the archive file (SPEC-0073). That is the intended lifecycle, and it is why dry-run is the
default: the first real run relocates 11 subtrees.

### Back-links

When a resolved spec's frontmatter has no `source_idea` and exactly one idea points at it,
`--apply` writes `source_idea: <IDEA-ID>` into the frontmatter. Ambiguity (two ideas claiming one
spec) is reported, never guessed.

*(As-built.)* The write inserts a **single line before the frontmatter's closing `---`**, not a
`yaml.safe_dump` round-trip. Re-dumping rewrites the entire block — flow-style `tags: [a, b]`
becomes a bullet list, `"M1: packaging"` becomes `'M1: packaging'` — turning a one-line
annotation into a large diff on a file the command was only asked to annotate. Two tests pin
this: one asserts the file differs by exactly one inserted line, one asserts a file with no
frontmatter is left alone.

### Surfacing drift

`report.next_ideas` and `hub_payload` gain a count of `advance`-able ideas: a `!` line under the
`wt next` panel and a `stale_ideas` integer in `wt.hub.v1`. Computed from the same
`reconcile_ideas` dry-run pass, so there is one definition of "out of sync".

## Alternatives considered

- **Derive state on read, drop it as stored truth** — cannot drift by construction, but
  `ideas.org` stops self-describing and every state-keyed hook (archival, `wt next`) needs
  rework. Rejected as a much larger change than the bug warrants.
- **Extend `wt spec sweep --internal`** — one command for users to learn, and the resolver
  already handles both kinds. Rejected because sweep's contract is *pull remote status into the
  outbox*; reconcile writes org state and pulls nothing. Same shape, different job.
- **Rewind ideas that are ahead of their spec** — most internally consistent, rejected as
  destructive: it would overwrite a deliberate manual state, unrecoverably.
- **Add a `SHIPPED` state** so `PROMOTED` stops meaning two things — genuinely clearer, deferred
  to keep this change to the bug.
- **Pre-commit hook running `--check-source-ideas`** — mechanical and unforgettable, but it
  reads a machine-local org file, so it fails on any checkout without one.
- **Definition-of-Done checklist item only** — cheapest, and exactly the mechanism that already
  failed for `IDEA-098`. Kept as a complement, not the fix.

## Acceptance criteria

- [x] `wt spec reconcile` with no flags writes nothing and exits 0, listing each idea whose
      state disagrees with its spec.
- [x] It reports the 11 known stale ideas (`IDEA-064`, `IDEA-077`…`IDEA-086`) as `advance` to
      `PROMOTED`.
- [x] `--apply` advances them, and a second `--apply` reports zero changes (idempotent).
- [x] A spec at `done` advances a `SPECCED` idea to `PROMOTED`.
- [x] A spec at `superseded` or `rejected` advances a pre-terminal idea to `DROPPED`.
- [x] A spec at `accepted`/`in-progress` advances an `IDEA`/`INCUBATE` idea to `SPECCED`, and
      leaves a `SPECCED` idea unchanged.
- [x] A spec at `draft`/`proposed` never changes an idea.
- [x] An idea already further along than its spec is reported as `flag-ahead` and its state is
      byte-identical afterwards, even with `--apply`.
- [x] An idea whose `:SPEC:` resolves to nothing is reported `missing` and does not abort the
      run.
- [x] Outbound-linked ideas resolve through the outbox and are reconciled by the same pass.
- [x] `--apply` writes `source_idea` onto a resolved spec that lacks it; two ideas claiming one
      spec is reported, not guessed.
- [x] Applying `PROMOTED`/`DROPPED` archives the subtree (SPEC-0073) and the idea is still
      resolvable afterwards.
- [x] `wt next` shows a stale count when drift exists and shows nothing when it does not.
- [x] `wt hub --json` includes `stale_ideas`; existing keys unchanged.
- [x] After `--apply`, `python3 tools/spec_lint.py --check-source-ideas` reports zero stale
      source ideas.
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_reconcile.py` (42 tests), fixtures building a tmp org + a
tmp specs dir:

- `test_dry_run_writes_nothing` — file bytes identical before/after; non-empty report.
- `test_status_to_state_matrix` — parametrised over every row of the Decision table
  (`done`, `superseded`, `rejected`, `accepted`, `in-progress`, `draft`, `proposed`) × the
  relevant starting states, asserting the resulting state. This is the spec's core contract, so
  it is enumerated rather than sampled.
- `test_apply_is_idempotent` — second `--apply` returns no `advance` rows and leaves bytes
  unchanged.
- `test_idea_ahead_of_spec_is_flagged_not_rewound` — `PROMOTED` idea + `accepted` spec:
  `flag-ahead`, state unchanged under `--apply`.
- `test_missing_spec_does_not_abort` — a bad `:SPEC:` between two good ideas; both good ones are
  still processed.
- `test_outbound_links_reconcile` — an idea pointing at an outbox `PROJ-NNNN` spec.
- `test_backlink_written_and_ambiguity_reported` — spec without `source_idea` gets one; two
  ideas claiming one spec reports instead of writing.
- `test_backlink_write_preserves_frontmatter_formatting` — the annotated file differs by exactly
  one inserted line; flow-style lists and quote style survive. Added after an early YAML
  re-dump mangled two real specs (see Rollout).
- `test_legitimate_terminal_states_are_not_flagged` — `EXPORTED`+`accepted`,
  `EXPORTED`+`in-progress`, `PROMOTED`+`accepted`, `PROMOTED`+`done` are the normal workflow and
  must not be flagged.
- `test_archival_on_apply` — applying `PROMOTED` moves the subtree to the archive file and the
  idea still resolves.
- `test_next_and_hub_surface_stale_count` — count appears with drift, absent without;
  `wt.hub.v1` keeps its existing keys.

**Manual verification**

1. `uv run wt spec reconcile` — lists 11, writes nothing; confirm `git status` on the org dir is
   unchanged in spirit (no state edits).
2. `uv run wt spec reconcile --apply` — 11 advance and archive.
3. `uv run python tools/spec_lint.py --check-source-ideas` — zero stale.
4. `uv run wt spec reconcile` again — zero changes.
5. `uv run wt next` — stale line gone.

**Regression guard**

Full `uv run pytest`, especially `tests/test_export.py` (sweep's outbound path must be
untouched), `tests/test_json_cli.py` (hub/next envelopes), and `tests/test_idea_freshness.py`
(reconcile bumps `:UPDATED:` via `set_state`, so freshness ordering shifts for reconciled ideas
— expected, and the archival tests must still hold).

## Clock Log

Clocked on IDEA-099 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

1. Land `reconcile_ideas` + the command; run the dry-run and read it. **Done** — reported
   exactly the 11, no false positives.
2. `--apply` once to clear the 11. **Done** — 11 advanced to `PROMOTED` and archived; a second
   run reports "every linked idea already matches its spec";
   `spec_lint.py --check-source-ideas` now reports **no stale source_idea states**.
3. Land the `wt next` / `wt hub` surfacing. **Done** — the drift line is gone and
   `wt hub --json` reports `stale_ideas: 0`.

**Incident during implementation.** An early version of `tests/test_reconcile.py` omitted
`specs_dir` from its fixture config. `_specs_dir` falls back to `Path.cwd()/docs/specs`
(`src/wt/specs.py:46`), so that test run resolved against this repo's **real** specs and
`_write_source_idea` wrote a bogus `source_idea` into
`docs/specs/0001-package-refactor-and-xdg-layout.md` and `0003-epic-and-subspec-model.md`,
reformatting their frontmatter in the process. Both files were reverted with `git checkout`, and
`git status` confirmed no other tracked file was touched. Two follow-on hardenings came out of
it: the minimal-insertion write above, and the formatting regression test. The underlying
footgun — a cwd-relative `specs_dir` default that lets any test with an incomplete fixture write
to the live repo — is *not* fixed here and is worth its own idea.

Reversible in the sense that state changes are visible in the org backups
(`data_dir/org-backups`), but archival moves subtrees between files — hence dry-run first.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Command vs derive-on-read* → a command; org state stays authxxitative.
- *Terminal state naming* → reuse `PROMOTED`; a distinct `SHIPPED` is deferred.
- *Status mapping* → the Decision table; `superseded`/`rejected` → `DROPPED`.
- *`in-progress`* → pulls a left-behind `IDEA`/`INCUBATE` up to `SPECCED`, else no-op.
- *Backwards drift* → flagged, never rewound.
- *Shape* → new `wt spec reconcile`; `wt spec sweep` untouched.
- *Safety* → dry-run default, `--apply` to write.
- *Prevention* → back-link writing + `wt next`/`wt hub` surfacing; no git hook, DoD line is a
  complement only.
