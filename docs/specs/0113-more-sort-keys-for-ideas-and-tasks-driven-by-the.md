---
id: SPEC-0113
title: "Sort on every column, driven by the key registry"
status: done
owner: user
created: 2026-07-31
updated: 2026-07-31
kind: feature
depends_on: [SPEC-0094, SPEC-0110]
milestone: "M5: interactive desk"
source_idea: IDEA-145
tags: [cli, tui, ideas, sort]
---

## Context

From `IDEA-145`: sorting offered only `freshness` and `priority`. That was a **deliberate v1
cut**, not a limitation — [SPEC-0094](./0094-optional-sort-on-wt-ideas-and-wt-tasks-not-global.md)'s
*Alternatives considered* says plainly: "Extra keys (project/state) — rejected for v1."

**The extension point was half-built.** `_apply_sort(rows, *, sort, desc, keys)` took a `keys`
registry that read like a plug-in table, then validated against a hardcoded
`("freshness", "priority")` and never consulted it. Adding an entry to the registry therefore did
**nothing on its own**; a new key meant four coordinated edits — registry, that tuple, the CLI
`Choice`, and the desk's cycle list.

## Goals / Non-goals

**Goals**
- Sort on **every column** the idea tables show; same vocabulary on CLI and desk.
- Validation driven by the registry, so a new key is one entry rather than four edits.
- `state` sorts by **workflow order**, not alphabetically.
- `wt tasks` gains the keys that make sense for it.

**Non-goals**
- Changing the default order (SPEC-0077 freshness stands).
- Sorting under `--query` (SPEC-0094: relevance wins) or in `wt next` / `wt hub`.
- Per-column sort *indicators* in the table header — the status line already names the sort.
- Multi-key sorting (`--sort project,priority`).

## Decision

`_apply_sort` validates from its `keys` registry. Each surface builds the registry with
`idea_sort_keys(cfg)` / `task_sort_keys(cfg)`, and the public names live in `IDEA_SORT_NAMES` /
`TASK_SORT_NAMES` — **tuples, not derived lists**, because Click builds its `Choice` at import
time before any cfg exists. A test asserts names and registries match exactly, so the pair that
used to drift cannot.

## Design

**Ideas** (`IDEA_SORT_NAMES`): `freshness · priority · state · project · kind · questions ·
created · id`. **Tasks** (`TASK_SORT_NAMES`): `freshness · priority · state · project · id`.

- **`state` → workflow order.** Ranks come from the configured `#+TODO` vocabulary
  (`org_idea_keywords` / `org_todo_keywords`) with the `|` separator dropped, so
  `IDEA < INCUBATE < SPECCED < PROMOTED`. Alphabetically `PROMOTED` lands between `INCUBATE` and
  `SPECCED`, interleaving live and finished work. Unknown states sort **last**, so a custom
  keyword still renders.
- **`project` → alphabetical, blanks last.** A missing project is *unknown*, not
  "alphabetically first".
- **`questions` → most open first.** The count you are triaging by is the interesting end.
- **`created` → newest first**, distinct from `freshness` (which is `:UPDATED:`); unstamped last.
- **Every key is a tuple ending in a stable tiebreaker**, so equal primaries keep a
  deterministic order instead of depending on file order.
- The registry is **cfg-bound** (closures), because `state` needs the keyword vocabulary and
  `questions` needs to read enrichment — neither is available to a bare `key(task)` function.
- Desk: `SORT_FIELDS = R.IDEA_SORT_NAMES`, so `o` cycles the same eight names the CLI accepts.

## Alternatives considered

- **Keep the hardcoded tuple and just extend it** — rejected: leaves the registry decorative and
  the four-edit trap in place.
- **Derive the Click `Choice` from the registry at runtime** — not possible: options are built at
  import time, before cfg. Hence constants plus a drift-guard test.
- **Alphabetical `state`** — rejected: nearly meaningless, and it interleaves live with done.
- **Expose only a curated subset** — the human asked for every column.

## Acceptance criteria

- [x] `wt ideas --sort` and `wt tasks --sort` accept every registered key, with `--desc`.
- [x] The desk's `o` cycle offers exactly the CLI's vocabulary.
- [x] `state` sorts by workflow order; unknown states last.
- [x] `project` puts blanks last; `questions` is most-open-first; `created` is newest-first.
- [x] `_apply_sort` validates from the registry; names and registries cannot drift.
- [x] The default order is unchanged.

## Test plan

**Executed 2026-07-31.** `tests/test_sort_registry.py` — 15 tests.

- **Drift guard (the load-bearing one):** `sort_key_names(idea_sort_keys(cfg))` equals
  `IDEA_SORT_NAMES`, same for tasks; `_apply_sort` accepts a made-up registry key and *rejects* a
  name absent from it; `default` is not selectable; the desk's `SORT_FIELDS` equals the CLI's.
- **End to end:** every name in both vocabularies runs through `wt ideas --sort N [--desc] --json`
  and `wt tasks --sort N --json`; an unknown name is rejected by Click and the error lists the
  vocabulary.
- **Per key:** `state` asserted against **states chosen so workflow and alphabetical genuinely
  disagree** (`IDEA, SPECCED, PROMOTED` vs `IDEA, PROMOTED, SPECCED`) — a first cut used data
  where the two coincided and proved nothing; unknown state ranks last and `|` is not a state;
  `project` blanks last and named ones alphabetical; `questions` descending; `created` newest
  first; `kind` and `id` ascending.
- **Invariants:** `--desc` reverses every key; every key is stable across repeated calls; the
  default order still equals `freshness` (SPEC-0077).
- **Manual verification** against the live org: `--sort project` grouped AI-workstreams first,
  `--sort state --all` led with `IDEA` rows rather than alphabetically, `--sort questions` led
  with the 11-open idea, and `--sort nonsense` listed the eight valid names.
- **Regression guard:** `uv run pytest` — 1008 passed; `tests/test_sort.py` (SPEC-0094) green, so
  the two original keys behave exactly as before.

One earlier test changed premise: `test_sort_hotkeys_cycle_and_reverse` assumed `o` toggled a
pair. It now walks the whole registry and asserts the wrap.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — all four resolved on IDEA-145 before promotion)
