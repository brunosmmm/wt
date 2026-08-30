---
id: SPEC-0070
title: "Automatic ideas.org rotation + terminal-idea archival"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-064
kind: epic
milestone: "M4: cli ergonomics"
tags: [org, maintenance]
---

## Context

Promoted from idea `IDEA-064` (ideas.org grows unbounded. how can we have files that are easily consumable? should we rotate idea files with newer ideas going to newer files, based on a length threshold?).

  :PROPERTIES:
  :ID: IDEA-064
  :PROJECT: Meta-Tools
  :END:
** Summary
Current state (measured): `ideas.org` is 1829 lines / `163KB with 86 top-level idea headlines. Of those, only `29 are still **live** (IDEA/INCUBATE/SPECCED); the rest — 40 PROMOTED, 9 EXPORTED, 7 DROPPED, 1 RESEARCHED — are terminal/settled but still sit in the same file forever.

Key finding from tracing the actual read/write paths: **reading and numbering are already file-agnostic** — `cfg['org_files']` is a directory (`~/work/org`), recursively globbed for every `**.org` under it (`_iter_org_paths`), and `next_idea_number()` scans `load_tasks(cfg)` (the full glob) for the max existing `:ID:`, not just one file. The **only* hardcoded single-file assumptions are: (1) `add_idea()` always writes new captures to the one fixed `cfg['org_ideas_file']` path, and (2) the two bulk `normalize-logs`/`normalize-questions` commands, when run with no selector, operate against that same single path rather than every idea-bearing file. Everything else (`wt ideas`, `wt next`, `wt hub`, `wt digest`) already works fine no matter how many `.org` files ideas are spread across.

This means the idea as posed actually bundles two somewhat separate problems:
1. **Raw growth** — the file keeps growing forever, eventually unwieldy to open/scroll/edit directly in an editor. This is what the idea's own proposed fix (rotate to a new file past a length threshold) targets directly.
2. **Signal-to-noise** — even a small file is cluttered if 57 of 86 entries are already terminal. `wt ideas`/`wt next` already filter these out by default at the CLI layer, but anyone opening the raw `.org` file directly still wades through all of it. Rotating by size alone doesn't fix this; it would take moving/archiving terminal-state entries out of the **active** file specifically.

Relevant prior decision: SPEC-0056's Alternatives-considered explicitly rejected a dedicated `wt idea archive` verb ("one generic close verb was preferred" — owner's call). Any rotation/archiving design here should stay mechanical/automatic rather than add a new manual per-idea verb, to stay consistent with that.

Existing precedent in this user's own org setup: `~/work/org/journal/` is already split into one directory-entry per day. But ideas don't arrive on a natural daily cadence (some days zero, some days many) — a count/size threshold (as the idea itself proposes) fits better than calendar-based splitting for this specific file.
** Open questions
*** RESOLVED Rotate by size/count threshold only (as originally proposed), or also/instead archive terminal-state (PROMOTED/EXPORTED/DROPPED/RESEARCHED) entries out of the active file regardless of size — these solve different problems (raw growth vs. signal-to-noise) and aren't mutually exclusive.
*** RESOLVED Should rotation/archiving be fully automatic (wt notices the threshold on a capture and starts a new file + updates config itself), or a manual maintenance command a human runs occasionally (e.g. wt idea rotate)?
*** RESOLVED normalize-logs/normalize-questions currently hardcode operating on the single org_ideas_file when run with no selector — they would silently miss ideas living in a second/third rotated or archived file. Does this need fixing as part of this work, or is it acceptable to defer?
** Log
*** [2026-07-26 Sun 16:42]
Decisions made:
1. Both fixes, not either/or — rotate the active file past a size/count threshold (raw growth) **and** archive terminal-state (PROMOTED/EXPORTED/DROPPED/RESEARCHED) entries out of the active file separately (signal-to-noise). They compose.
2. Fully automatic — wt checks the threshold itself on capture and rotates/archives without a human needing to remember a maintenance command.
3. normalize-logs/normalize-questions get fixed as part of this work, **but** — important constraint from the owner — the actual file-rewrite (moving headlines between files during rotation/archival) must be done by deterministic, testable code (a real tool/function with tests), never by an agent manually cutting/pasting org text. This matches the existing pattern in org_write.py (line-anchored, drift-guarded, atomic-write helpers like set_property/set_state) rather than ad-hoc LLM-driven edits — rotation/archival should be just another such primitive, not a one-off agent action.

## Goals / Non-goals

**Goals**
- Stop `ideas.org` (or any single idea-bearing file) from growing forever: once it crosses a
  configurable size threshold, automatically roll it over into a dated historical file and
  start a fresh active file at the same configured path.
- Automatically move an idea's whole subtree out of the active file into a dedicated archive
  file the moment it becomes terminal — `DROPPED`/`RESEARCHED` (via `wt idea close`),
  `PROMOTED` (already fully handed off to generated org tasks), and `EXPORTED` whose linked
  outbound spec's status has become `done` (via `pull-status`/`sweep`) — so a human opening the
  active file directly sees only what's still actually live.
- Both mechanisms run automatically, with zero new command a human has to remember to run.
- All file-rewriting (rotation renames, subtree excise-and-append) goes through new,
  deterministic, tested primitives in `org_write.py`, mirroring its existing line-anchored +
  drift-guarded + atomic-write pattern (`set_property`/`set_state`) — never an ad-hoc/agent-
  driven rewrite of org text.
- Fix `wt idea normalize-logs`/`normalize-questions` (no-selector mode) to scan every
  idea-bearing file under `cfg['org_files']`, not just the single `cfg['org_ideas_file']` path —
  otherwise they'd silently stop covering ideas the moment rotation/archival creates a second
  file.

**Non-goals**
- No new user-facing manual verb for archiving a single idea (e.g. `wt idea archive <id>`) —
  SPEC-0056 already rejected verb proliferation in favor of the generic close model; this stays
  a side effect of existing state transitions, not a new thing to invoke.
- Not changing `wt ideas`/`wt next`/`wt hub`/`wt digest` — these already read via `load_tasks`'s
  directory glob and already filter out non-live states by default; they need no changes to
  keep working once ideas are spread across more files.
- Not retroactively rotating/archiving the current real `ideas.org` as part of any child spec's
  automated test suite — that's a one-off manual run against real data after the code lands
  (mirrors how SPEC-0064's outbound backfill was run manually, not as a test).
- Not a general-purpose org-file-splitting library for arbitrary files — scoped specifically to
  the idea-capture file(s) `wt` itself manages.

## Decision

Two independent, deterministic primitives — file rotation (whole-file rollover past a size
threshold) and subtree archival (cut one idea's headline+body out of its file, append to an
archive file) — both built as new `org_write.py` functions in the same style as existing
line-anchored/drift-guarded/atomic-write helpers. Rotation hooks into `add_idea()` (checked on
every capture). Archival hooks into the existing state-transition call sites that already mark
an idea terminal (`set_state`, plus `pull_status`/`sweep` for the EXPORTED-becomes-done case) —
so both fire automatically, with no new command surface.

## Architecture / cross-cutting design

- **Rotation primitive:** a new `org_write.py::maybe_rotate_ideas_file(cfg)` — after `add_idea`
  writes, count lines in `cfg['org_ideas_file']`; if over a configurable threshold (new config
  key, default ~1200 lines), atomically rename the file to a dated historical name
  (`ideas-YYYYMMDD.org`) and write a fresh file at the *original* configured path with just the
  `#+TODO` header. `cfg['org_ideas_file']` never changes — new captures always target the same
  configured path, so no config mutation is needed. The renamed historical file stays under the
  same `org_files` directory root, so `load_tasks`'s existing recursive glob (`_iter_org_paths`)
  picks it up automatically — nothing else needs to know rotation happened.
- **Archival primitive:** a new `org_write.py::archive_idea(cfg, task)` — extracts the idea's
  exact line range (its headline through the line before the next same-or-higher-level
  headline, i.e. the whole subtree: properties, Summary, Open questions, Log, everything),
  removes those lines from the source file (atomic write, drift-guarded the same way
  `set_property` is — re-check the headline hasn't changed since `task` was parsed), and
  appends the extracted block into a dedicated archive file (`cfg['org_ideas_archive_file']`,
  new config key, e.g. `~/work/org/ai/ideas-archive.org`; created with the same `#+TODO` header
  convention if it doesn't exist yet, matching `add_idea`'s existing bootstrap pattern).
  Lossless: every property, Summary/Log/questions line moves verbatim.
- **Automatic archival hooks:** `set_state(cfg, task, new_state)` gains an optional check —
  when `new_state` is in a configured terminal-idea-states set (`DROPPED`, `RESEARCHED`,
  `PROMOTED`) *and* `task.is_idea`, call `archive_idea` immediately after the state write
  succeeds. `pull_status`/`sweep` (`export.py`) gain the same check specifically for the
  EXPORTED case: when a pulled status is `"done"` and the idea's own org state is `EXPORTED`,
  archive it right there — this is the one terminal condition that isn't visible from the
  idea's own state field (the idea stays `EXPORTED` forever; only the *linked outbound spec's*
  frontmatter status changes), so it has to be checked at the point that status is learned.
- **`normalize-logs`/`normalize-questions` fix:** when called with no selector, both currently
  do `path = cfg.get("org_ideas_file")` and operate only on that one file
  (`explore.py` ~L317-322, ~L391-395). Change both to iterate every file returned by
  `load_tasks`'s underlying file enumeration (i.e. every distinct file any idea task currently
  lives in) instead of the single hardcoded path.

## Breakdown / sub-specs

- [x] SPEC-0071 — File-rotation primitive (`maybe_rotate_ideas_file`) wired into `add_idea`,
      with a configurable line-count threshold. — **done**
- [x] SPEC-0072 — Idea-archival primitive (`archive_idea`): atomic, drift-guarded subtree
      excise-and-append, with its own dedicated archive file/config key. — **done**
- [x] SPEC-0073 — Automatic archival hooks: wire `archive_idea` into `set_state`'s terminal
      states (DROPPED/RESEARCHED/PROMOTED) and into `pull_status`/`sweep`'s EXPORTED-becomes-
      done case (depends_on SPEC-0072). — **done**
- [x] SPEC-0074 — Fix `normalize-logs`/`normalize-questions` (no-selector mode) to scan every
      idea-bearing file instead of the single `org_ideas_file` (depends_on SPEC-0071/SPEC-0072
      only in the sense that there's nothing to fix against until multiple files can exist for
      real — the code change itself has no hard dependency). — **done**

Sequencing / dependencies: SPEC-0071 and SPEC-0072 are independent, foundational primitives —
can land in either order or in parallel. SPEC-0073 depends on SPEC-0072 (needs `archive_idea`
to exist). SPEC-0074 has no hard code dependency but is sequenced last since it's only
meaningfully testable once rotation/archival can actually produce a second idea-bearing file.

## Acceptance criteria

- [x] Once `ideas.org` crosses the configured line threshold, the next capture rotates it: the
      old content is preserved verbatim under a new dated filename, and a fresh file exists at
      the original configured path — with zero config change required.
- [x] An idea closed as `DROPPED` or `RESEARCHED`, one advanced to `PROMOTED`, and one whose
      linked outbound spec's status is pulled as `done` while the idea is `EXPORTED`, are each
      automatically moved out of the active file into the archive file — losslessly, with no
      manual step.
- [x] `wt ideas`/`wt next`/`wt hub`/`wt digest`/ID numbering all continue to behave identically
      whether an idea lives in the active file, a rotated historical file, or the archive file.
- [x] `wt idea normalize-logs`/`normalize-questions` (no-selector mode) cover ideas in every
      idea-bearing file, not just the originally-configured one.
- [x] All file mutation goes through tested `org_write.py` primitives — no code path performs
      an ad-hoc/manual rewrite of org text for rotation or archival.

## Test plan

- **Integration/e2e tests:** capture enough fixture ideas to cross a (test-scale) rotation
  threshold and assert the rollover happens correctly and content is preserved; close/promote/
  export-and-pull-done fixture ideas and assert each lands in the archive file with full
  fidelity (properties, Summary, Log, questions intact); assert `wt ideas`/`wt next`/ID
  numbering are unaffected by ideas living across active/rotated/archive files; assert
  `normalize-logs`/`normalize-questions` reach ideas in a second file. Per-primitive unit
  coverage (rotation, archival, each hook, the normalize fix) lives in its child spec.
- **Manual verification:** once all children land, manually run the real `ideas.org` through a
  dry pass (or wait for the next real rotation/archival trigger) and eyeball the result.
- **Regression guard:** full `uv run pytest` green; existing single-file behavior (today's
  common case, file never crossing the threshold) is byte-identical to before.

## Rollout / sequencing

1. SPEC-0071 (rotation) and SPEC-0072 (archival primitive) land first, independent of each
   other.
2. SPEC-0073 (automatic archival hooks) lands once SPEC-0072 exists.
3. SPEC-0074 (normalize-* fix) lands last, once there's a real second file to test against.

## Definition of done

- [x] All child specs `done` or `superseded` (the linter gates this).
- [x] Integration test plan executed; `uv run pytest` green.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

- None blocking — all three questions raised during explore were resolved: rotation and
  archival are both in scope (they solve different problems); both run fully automatically;
  and the normalize-* gap is fixed now, with file rewrites required to go through deterministic,
  tested primitives rather than agent-driven edits.
