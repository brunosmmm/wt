---
id: SPEC-0114
title: "Hierarchical idea view: project > epic > idea"
status: done
owner: user
created: 2026-07-31
updated: 2026-07-31
kind: feature
depends_on: [SPEC-0110, SPEC-0113]
milestone: "M5: interactive desk"
source_idea: IDEA-141
tags: [tui, cli, ideas, hierarchy]
---

## Context

From `IDEA-141`: show ideas as a tree rather than a flat list, in `wt ideas` and the desk.

**Exploration measured the corpus rather than assuming a tree existed** (151 ideas, 114 internal
specs, 10 epics):

| edge | coverage |
|---|---|
| `:PROJECT:` | **131 / 151** (87%) |
| epic→child, derived from spec `parent:` | **33** edges across 8 parents (widest: IDEA-095 ×8, IDEA-128 ×6) |
| `FOLDED_INTO` / `SUPERSEDED_BY` | **1 each** — effectively unused |
| no hierarchy edge at all | **110 / 151** |

Depth is exactly **1**: the spec model is epic → child with no grandchild nesting. So the idea's
original framing — "which edge defines the tree" — was the wrong question. An epic-only tree
renders 8 clusters and 110 loose ideas; project alone discards the one real parent/child relation.

**Qualification found while implementing.** The **epic level only materialises with `--all`**.
Children are PROMOTED as they ship, so they leave the default open view: measured **0**
epics-with-children on the open corpus (39 ideas) versus **5** on the full one (151). Day to day
this is therefore `project > idea`, with the third level appearing on `--all`. The design stands,
because project grouping was always the level with reach — but "project > epic > idea" oversells
the default view, and that is recorded rather than glossed.

Whether an open epic should pull its *done* children in as context is a change to what a
filtered view means, so it is **left open for the human** rather than decided here.

## Goals / Non-goals

**Goals**
- A **project > epic > idea** view: 3 levels, in `wt ideas` and the desk.
- Orphans hang directly under their project; project-less ideas collect under `(no project)`.
- Filtered/searched views keep **ancestors as dim context**.
- Compose with SPEC-0113 sorting rather than replacing it.

**Non-goals**
- A schema change — every edge is already derivable (see Decision).
- Closure pointers (`folded_into` / `superseded_by`) as tree edges: they express supersession,
  not containment, and there are 2 in the whole corpus.
- Arbitrary depth, or grandchild nesting the spec model cannot express.
- A selectable grouping axis (state/kind/…): every axis except project and epic is really a sort
  with headers, which SPEC-0113 already gives.
- Making tree the default view; it is a mode.
- Tree in the hub tab, `wt next`, or `wt tasks`.

## Decision

**Group project > epic > idea, computed at render time.** No new JSON: the edges come from
`spec` on the idea row plus `parent` on the spec — both already in the envelopes, and `wt hub`
already exposes the latter.

**Structure is a forest, not a DAG.** Spec `parent:` is single-valued, so every idea has at most
one derived parent. That is what makes a plain tree correct rather than a compromise.

### Decided by the assistant, not the human — overturnable

1. **One spec, not an epic.** Precedent: SPEC-0110 carried planner + filters + sort + wide mode.
   The grouping model is shared by both surfaces, so splitting fragments one change.
2. **Sort composition:** leaves sort by the SPEC-0113 key *within* their group; **groups sort by
   their own best member under the same key**. The key should mean the same thing at every level,
   and stable-alphabetical groups would bury active work under "AI-workstreams" permanently.
   `(no project)` sorts **last** always, matching SPEC-0113's blanks-last rule for `project`.

## Design

- `report.build_idea_tree(cfg, tasks, *, sort=None, desc=False)` → ordered
  `[{project, count, epics: [{idea, count, children: [...]}], loose: [...]}]`. A pure function
  over tasks the caller already collected, so filters/search apply *before* grouping and the tree
  never re-queries.
- **Ancestors as context:** a group or epic is rendered whenever any descendant survives the
  filter, and is marked `matched: False` when it did not match itself — the renderer dims those.
  Without this a matched child appears with no indication of its epic, losing the context the
  tree exists to give.
- **CLI:** `wt ideas --tree`. Indentation is charged against the same heading budget SPEC-0110's
  planner computes, so a deep row cannot silently crop; group headers carry a count.
- **Desk:** a key toggles tree mode; the row set becomes the flattened tree with a depth per row.
  Auto-drop still applies, with indentation subtracted from the heading floor.
- Counts on group headers are **descendant idea counts**, not direct children — the useful number
  when triaging a project.

## Alternatives considered

- **Epic > idea only** — rejected: 8 clusters, 110 loose ideas, mostly flat.
- **Project > idea only** — rejected: discards the only real parent/child relation.
- **Selectable grouping axis** — rejected: more work, and every axis but project/epic is a sort
  with headers.
- **Closure pointers as edges** — rejected: supersession is not containment, and 2 edges exist.
- **Flatten while filtered** — rejected: loses grouping exactly when narrowing.
- **Only fully-matching branches** — rejected: silently hides matching children.

## Acceptance criteria

- [x] `wt ideas --tree` groups project > epic > idea, with `(no project)` last.
- [x] Group headers show descendant counts.
- [x] Filters/search keep ancestors, marked as unmatched context.
- [x] `--sort` orders leaves within a group and groups by their best member; `--desc` reverses.
- [x] The desk can toggle tree mode; indentation is charged against the heading budget.
- [x] Every idea appears exactly once; no idea is lost or duplicated.
- [x] Flat output is unchanged when `--tree` is absent.

## Test plan

**Executed 2026-07-31.** `tests/test_idea_tree.py` — 16 tests, on a corpus-shaped fixture (an
epic with 2 children + a loose sibling under one project, a second project, a project-less idea).

- **Shape:** derived epic edges are exactly the spec-`parent:` pairs; the epic nests its two
  children while the loose idea sits directly under the project; `(no project)` sorts last;
  counts are **descendant** counts (epic 3, project 4).
- **The load-bearing invariant:** every input idea appears **exactly once** — asserted against
  the collector's own id list, with a duplicate check. A shape assertion alone would not notice a
  dropped or doubled row.
- **Ancestors as context:** feeding only a child yields its epic pulled in with
  `matched=False` and the child `matched=True` — a matched child is never orphaned.
- **Sort composition:** applies within groups for several keys; groups order by their best member
  (`--sort id` puts the group holding the lowest id first); a bad sort name raises.
- **CLI:** `--tree` renders group headers and nesting in order; flat output has no headers and is
  unchanged; `--tree` composes with `--project` and with **every** `IDEA_SORT_NAMES` key;
  `--json` output is **byte-identical** with and without `--tree`, since it is a view mode and
  the agent contract must not move.
- **Desk:** `flatten_tree` returns leaves only with correct depths and project labels; `g`
  toggles and **neither adds nor loses ideas**; the status line says `tree`; indentation is
  charged against the heading budget, so a long nested heading **ellipsises rather than cropping**.
- **Manual verification** on the live corpus: `wt ideas --tree` grouped 8 projects with
  `(no project)` last; `--tree --all` revealed nesting (IDEA-095 with 9 descendants, IDEA-128
  with 6); `--tree --all --sort questions` put Example-Tests first because it holds the 11-open
  idea — best-member ordering working; the desk at 120×20 showed IDEA-095's children indented
  with the project column labelling groups.
- **Regression guard:** `uv run pytest` — 1026 passed; SPEC-0110/0113 suites green.

## Decided during implementation

**The desk emits no synthetic group-header rows.** It already has a `project` column that labels
each group, so a header row would duplicate it *and* force every mutation path (`selected_id`,
row keys, focus, refresh) to special-case a row with no idea behind it. Rows are grouped by order
and indented by epic depth instead — same structure, one row type. The CLI does render explicit
headers, because its tree view has no project column. A first attempt emitted `task=None` header
rows and broke `paint` immediately.

`tree` could not be used as the attribute name: it collides with Textual's read-only
`DOMNode.tree`. Hence `tree_mode`.

## Rollout / sequencing

1. `build_idea_tree` + tests (pure, no UI).
2. `wt ideas --tree`.
3. Desk toggle.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — all four resolved on IDEA-141; the two assistant-decided items are flagged in Decision)
