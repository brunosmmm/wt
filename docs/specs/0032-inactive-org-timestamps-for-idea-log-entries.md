---
id: SPEC-0032
title: Inactive org timestamps for idea Log entries
status: done
owner: user
created: 2026-07-23
updated: 2026-07-23
milestone: "M4: cli ergonomics"
kind: feature
tags: [ideas, org, explore, ergonomics]
source_idea: IDEA-020
depends_on: [SPEC-0031]
---

## Context

Promoted from idea `IDEA-020`.

[SPEC-0031](./0031-rename-idea-explore-to-log-datetime-log-stamps.md) changed Log entry
headlines from date-only to `*** YYYY-MM-DD HH:MM`. That is still not org-native. Org-mode
distinguishes **active** `<…>` (agenda-visible) from **inactive** `[…]` (recorded, not
agenda). Idea Log notes must not pollute agenda; task `SCHEDULED`/`DEADLINE` already use
active stamps via `_org_date`, and `CLOSED:` already uses inactive via `_closed_stamp`.

## Goals / Non-goals

**Goals**
- New `wt idea log` entries use a level-3 headline whose text is an **inactive** org
  timestamp with day name and time: `*** [YYYY-MM-DD Day HH:MM]`, note body underneath
  (same layout as today).
- Share formatting with `CLOSED:` via a small helper (e.g. `_inactive_stamp(cfg, *,
  with_time=False|True)`); Log uses `with_time=True`.
- `wt idea normalize-logs` rewrites historical plain `*** YYYY-MM-DD[ HH:MM]` heads to
  inactive stamps (idempotent).
- Tests assert the inactive bracket form (and that active `<…>` is not written).

**Non-goals**
- List-bullet Log layout.
- Active timestamps on Log entries.
- Changing `SCHEDULED`/`DEADLINE` writers, agenda bucketing, or adding time-of-day /
  repeaters to planning lines (separate work).
- Changing `CLOSED:` to include time (optional later; not required here).

## Decision

Keep the `***` entry + body structure. Replace the plain datetime headline with an
inactive org timestamp including weekday and `HH:MM`. Provide `wt idea normalize-logs`
to rewrite historical plain heads in place (forward-only new writes plus optional
backfill).

## Design

### Stamp helper (`src/wt/org_write.py`)

```python
def _inactive_stamp(cfg, *, with_time=False):
    now = dt.datetime.now(cfg.get("_tz"))
    if with_time:
        return now.strftime("[%Y-%m-%d %a %H:%M]")
    return now.strftime("[%Y-%m-%d %a]")
```

`_closed_stamp` becomes a thin wrapper around `_inactive_stamp(cfg)` (behavior unchanged:
date + weekday, no time).

### `append_log` (`src/wt/explore.py`)

- Default headline: `*** {_inactive_stamp(cfg, with_time=True)}`
- Explicit `when=` (tests): if the caller passes a string that is already a full inactive
  stamp, use as-is; if they pass a datetime/`YYYY-MM-DD HH:MM` for tests, format into
  `[…]` — simplest test path: allow `when=` to be the *full headline suffix* after `*** `
  (document that), or pass a `datetime` and format. Prefer: `when=None` → stamp now;
  `when=datetime` → format that instant; string `when` only for exact override in tests
  (must look like `[…]` or be wrapped).

Keep note body + `to_org_body` as today.

### Migration (`normalize_plain_log_headlines` / `wt idea normalize-logs`)

Rewrite lines matching `*** YYYY-MM-DD` or `*** YYYY-MM-DD HH:MM` to
`*** [YYYY-MM-DD Day]` / `*** [YYYY-MM-DD Day HH:MM]`. Skip lines that already use
`[…]`. Default target: `org_ideas_file`; optional idea selector rewrites that idea's file.

### Tests

Update `test_log_stamp_includes_time` to expect
`*** [YYYY-MM-DD Day HH:MM]\n` (regex). Confirm no `<` active stamps in new Log lines.

## Alternatives considered

- **List bullets `- [stamp] note`** — deferred; hurts multi-line notes and changes layout.
- **Active `<stamp>` headlines** — rejected; agenda pollution.
- **Migrate old Log heads** — rejected; low value; mixed history is fine.
- **Leave SPEC-0031 plain datetimes** — rejected; user wants org-native inactive stamps.

## Acceptance criteria

- [x] New Log entries are `*** [YYYY-MM-DD Day HH:MM]` with the note as the entry body.
- [x] Stamps use `[]` (inactive), never `<>` (active).
- [x] `CLOSED:` stamps remain inactive date+weekday (no required behavior change).
- [x] `wt idea normalize-logs` rewrites plain historical Log heads; idempotent.
- [x] Tests + full pytest green.

## Test plan

- **Automated:** `tests/test_explore.py` — inactive stamp regex + `_inactive_stamp` +
  `normalize_plain_log_headlines`.
- **Manual:** `wt idea normalize-logs` on real ideas.org; spot-check rewritten heads;
  re-run → 0 rewritten.
- **Regression:** `uv run pytest` green after ledger refresh.

## Rollout / migration

New writes use inactive stamps. Run `wt idea normalize-logs` once per ideas file to
backfill. Old plain heads remain readable until normalized.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; pytest green; manual check noted.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

_None._
