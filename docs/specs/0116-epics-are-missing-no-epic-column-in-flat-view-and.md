---
id: SPEC-0116
title: "Epics: expose :EPIC: in rows, flat column, filter, and as the tree's epic level"
status: done
owner: user
created: 2026-08-01
updated: 2026-08-01
kind: feature
depends_on: [SPEC-0110, SPEC-0114, SPEC-0115]
milestone: "M5: interactive desk"
source_idea: IDEA-168
tags: [tui, cli, epic, bug]
---

## Context

Reported: epics are missing entirely — the flat view never says an idea is under an epic, and the
tree should have epics as a level.

**The second point exposes a research failure in SPEC-0114.** That spec measured `:SPEC:`,
`:PROJECT:`, `FOLDED_INTO` and `SUPERSEDED_BY`, then *derived* epic-ness from spec `parent:`
(idea → `:SPEC:` → parent spec → `source_idea`) and concluded "33 edges, mostly flat, and the
epic level only materialises with `--all`". **It never measured `:EPIC:`.**

Corpus truth, measured 2026-08-01:

| fact | value |
|---|---|
| ideas carrying a stored `:EPIC:` | **64 of 166** |
| distinct epics | **12** |
| open ideas carrying `:EPIC:` | **10 of 43** (derived parentage gave **0**) |
| what `:EPIC:` points at | a **spec id**, internal (`SPEC-0087`) *and* outbound (`EXAMPLE-0007`, `DEMO-0001`) |
| `:EPIC:` values that are idea ids | **0** — the edge is idea → *spec*, not idea → idea |

So the relation the human means exists, is first-class, is stored rather than derived, covers
outbound projects (which spec-parentage never could), and — unlike derived parentage — is
**visible in the default open view**.

## Goals / Non-goals

**Goals**
- `idea_row` exposes `epic` (additive to `wt.ideas.v1` / `wt.idea.v1`).
- The flat table shows an `epic` column, on the conditional-column precedent of `pri` / `q`.
- `--epic` filters `wt ideas`, and joins the desk's in-app filter vocabulary.
- The tree's epic level groups by `:EPIC:`.
- Derived spec-parentage nesting **is kept**, so the epics that already render do not regress.

**Non-goals**
- Writing `:EPIC:` from the desk (capture already accepts `--epic`; a mutator is separate work).
- Resolving an epic spec id to its title — the id is what the user typed and what `wt spec` uses.
- Validating that an `:EPIC:` target exists (SPEC-0018's association contract is permissive).
- Changing `wt tasks`, `wt next` or the hub.

## Decision

**`:EPIC:` is the epic relation**, exposed everywhere ideas are listed. The tree keys its epic
level on `epic_key(task)`: the stored `:EPIC:` when present, else the derived parent-idea id from
SPEC-0114, else none. Two node kinds share one level — a **spec-id epic** and a **parent-idea
epic** — which keeps the nesting that already works while adding the relation that was missing.

## Design

- `idea_row["epic"]` from `:EPIC:`, omitted when blank (matching `project` / `spec`).
- `_IDEA_META_COLS["epic"]` with a cap so the planner can squeeze it; shown only when some listed
  idea has one, exactly like `pri` and `q`. Desk adds it to `DESK_COLUMNS`, and to `DROP_ORDER`
  *after* `project` — an epic is more specific than a project and less recoverable at a glance.
- `filter_tasks(..., epic=…)` and `collect_idea_tasks(..., epic=…)`; `wt ideas --epic`, plus
  `epic` in the desk's `FILTER_KEYS` so `f` accepts `epic=EXAMPLE-0007`.
- `build_idea_tree` groups project → **epic key** → idea. An epic node's label is the `:EPIC:`
  spec id, or the parent idea's id + heading when it came from derived parentage.

## Decided during implementation

Recorded here as they were made, rather than after the fact — changing an approved design
mid-implementation without flagging it is exactly what produced the SPEC-0114 tree defect.

1. **A `:EPIC:` node is synthetic.** The stored `:EPIC:` points at a *spec id*, and no such idea
   exists (measured: **0** of the 12 epic values is an idea id). So that level's node has no
   `task`, no state, no kind. It renders as a **plain label** — `▾ EXAMPLE-0007  6` — rather than
   as an idea row: the first cut reused the idea renderer and produced
   `EXAMPLE-0007 💡 EXAMPLE-0007`, duplicating the id and borrowing a kind glyph from its first child.
   The desk applies the same rule, returning a `magenta` label for synthetic nodes.
2. **A synthetic node sorts by its first child.** It carries `task = children[0]["task"]` purely
   so the existing leaf-key ordering applies to it — consistent with SPEC-0114's rule that groups
   order by their best member. It is a deliberate stand-in, not an accident.
3. **Two node kinds share one level.** A parent *idea* (SPEC-0114's derived nesting) and a
   *spec id* (`:EPIC:`) both appear as epic nodes. Merging them keeps existing nesting working
   while adding the missing relation, at the cost of the level being heterogeneous — consumers
   must check `synthetic` rather than assume every epic node has an idea behind it.

## Alternatives considered

- **Keep deriving epics from spec `parent:`** — rejected: it is a proxy for a relation that is
  stored directly, misses outbound projects entirely, and yields zero nesting in the open view.
- **Replace derived parentage entirely** — rejected: it would remove nesting the human has
  already seen working (IDEA-095's 8 children).
- **Resolve epic ids to titles** — deferred: needs a lookup across internal specs *and* the
  outbox, for cosmetic gain.

## Acceptance criteria

- [x] `wt ideas --json` rows carry `epic` when set.
- [x] `wt ideas` shows an `epic` column when any listed idea has one, and omits it otherwise.
- [x] `wt ideas --epic X` filters; the desk's `f` bar accepts `epic=X`.
- [x] The desk table shows the epic column.
- [x] The tree groups ideas under their `:EPIC:` as a level, in the **default open view**.
- [x] Derived spec-parentage nesting still works.
- [x] Flat output unchanged when no idea has an epic.

## Test plan

**Executed 2026-08-01.** `tests/test_epic_view.py` — 13 tests.

- **Row/JSON:** `epic` present when set, omitted when blank (matching `project` / `spec`).
- **Flat column:** shown when any listed idea has an epic, omitted otherwise — asserted on the
  **header row**, because searching the whole table gave a false positive: a seeded heading
  contained the word "epic" and the omission test passed wrongly.
- **Filter:** `--epic` matches `collect_idea_tasks(epic=…)` and the equivalent `--json`; unknown
  epic yields nothing; `epic` is in the desk's `FILTER_KEYS` and `f` accepts `epic=EXAMPLE-0007`.
- **Tree, the decisive case:** stored `:EPIC:` groups **in the default open view** — the exact
  case SPEC-0114's derived parentage could not produce (zero epics-with-children there). The node
  is marked `synthetic`, its children are right, and its count is right.
- **No regression:** derived spec-parentage still nests real ideas (`synthetic` absent); a stored
  `:EPIC:` wins over derived parentage when both apply; an idea with neither sits directly under
  its project; **every idea still appears exactly once** now that two node kinds share the level.
- **Rendering:** the CLI tree prints an epic as a label — asserted that the id is not duplicated
  and no kind glyph is borrowed, the exact defect of the first cut.
- **Manual verification in a real terminal** (pty + pyte, 120×32): `▶ EXAMPLE-0007  (7)` renders as
  a collapsible level in the **default** open view, and the flat table shows the `epic` column.
- **Regression guard:** `uv run pytest` — 1045 passed; SPEC-0110/0113/0114/0115 suites green.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed in a real terminal.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none)
