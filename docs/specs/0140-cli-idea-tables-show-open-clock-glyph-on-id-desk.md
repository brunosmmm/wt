---
id: SPEC-0140
title: "CLI idea tables show open-clock glyph on id (desk parity)"
status: done
owner: user
created: 2026-09-02
updated: 2026-09-02
milestone: "M4: cli ergonomics"
kind: feature
tags: [cli, clock, ideas]
depends_on: [SPEC-0103, SPEC-0075]
source_idea: IDEA-344
---

## Context

[SPEC-0103](./0103-metadata-clock-and-idea-json-parity-for-the-desk.md) marks a running
clock on the **desk** id cell with cyan `◕ ` (two-space pad when idle) so operators do not
forget an open session. JSON rows already carry `clock_open` / `clocked_hours` via
`idea_row`.

The Rich tables for `wt ideas` and `wt next` (and `--tree`) still render a plain dim id
(`src/wt/report.py`). Scanning those lists hides open clocks even though the same
`idea_row` knows `clock_open`. Reported as IDEA-344.

## Goals / Non-goals

**Goals**

- Human CLI idea lists show the same open-clock mark as the desk: `◕ ` on the id when
  `clock_open`, two spaces otherwise.
- Cover flat `wt ideas`, `wt next`, and `wt ideas --tree`.
- Width planning reserves space for the glyph (no headline steal / mid-glyph clip).

**Non-goals**

- A dedicated clock column.
- Changing desk glyphs or JSON schema.
- Changing clock-in/out semantics.
- Stronger desk mark (deferred).

## Decision

Reuse SPEC-0103’s id-prefix convention on CLI Rich surfaces. Introduce a small display
helper and an `_id` field on each printed row (same pattern as `_kind` / `_age`) so
`_meta_widths` measures the glyph+id string. JSON output stays unchanged (agents already
read `clock_open`).

## Design

**Helper** in `src/wt/report.py`:

```python
def _idea_id_label(prow) -> str:
    """`◕ ` + id when clock_open, else two spaces + id (SPEC-0103 / SPEC-0140)."""
    prefix = "◕ " if prow.get("clock_open") else "  "
    return prefix + (prow.get("id") or "")
```

**Before width plan / render** (in `ideas` and `next_ideas` loops that build `prows`):

```python
prow["_id"] = _idea_id_label(prow)
```

**`_meta_widths`:** map `"id"` → measure `"_id"` (like `updated`→`_age`, `kind`→`_kind`).
Bump id `min_width` from 8 → 10 so `  IDEA-NNN` always fits the pad.

**Render:**

- Flat tables: id cell uses `_id` with cyan when `clock_open`, else dim.
- `_print_idea_tree`: prefix `node['row']` the same way before printing the id.

**Tests:** extend an ideas/next table test (or `tests/test_clock_json_parity.py` /
`test_idea_table_width.py`) — clock-in one idea, capture Rich output / plain render,
assert `◕` appears next to that id and not next to an idle sibling; width planner
includes glyph length.

## Alternatives considered

- **New `clock` column** — rejected: wastes width; SPEC-0103 already chose id mark.
- **Only document “use the desk”** — rejected: CLI is the daily scan for many operators.
- **Change desk to a louder glyph** — out of scope; desk already has the mark.

## Acceptance criteria

- [x] `wt ideas` Rich output prefixes a `clock_open` idea’s id with `◕ ` and pads idle ids.
- [x] `wt next` does the same.
- [x] `wt ideas --tree` shows the glyph on clocked idea nodes.
- [x] `wt ideas --json` / `wt next --json` unchanged (still `clock_open` bool, no glyph in id).
- [x] Automated test covers at least flat `ideas` output with one open clock.
- [x] Desk behaviour unchanged.

## Test plan

- **Automated:** seed two ideas; `clock_in` one; call `report.ideas` / `report.next_ideas`
  with a fixed console width (or capsys); assert `◕` only on the clocked id. Assert JSON
  id strings have no glyph. Optional: `_meta_widths` / `_idea_id_label` unit asserts.
- **Manual:** `wt idea clock-in IDEA-…`; `wt ideas`; `wt next`; confirm cyan/glyph; clock-out.
- **Regression:** `uv run pytest tests/test_idea_table_width.py tests/test_clock_json_parity.py`.

## Rollout / migration

None — display-only.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual check noted.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

None.
