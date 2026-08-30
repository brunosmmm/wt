---
id: SPEC-0028
title: All-time topics rollup by facet axis
status: done
owner: user
created: 2026-07-22
updated: 2026-07-22
milestone: "M4: cli ergonomics"
kind: feature
tags: [cli, reporting, topics, ergonomics]
source_idea: IDEA-014
depends_on: [SPEC-0027]
---

## Context

Promoted from idea `IDEA-014`.

`wt topics` lists every base topic with `bucket=` repeated on the right. After
[SPEC-0027](./0027-prefix-facet-inheritance-for-colon-suffixed-topics.md) inheritance,
children show the parent bucket but the table is still one row per base topic. The user
wants the same all-time hours/share view **condensed so rows are buckets** (Example,
AI-workstreams, …).

`wt report --by bucket` already regroups by facet, but is day/week/last-N scoped — not a
topics-style all-time (or `--last N`) rollup. Command shape was left open; we pick
**`wt topics --by <axis>`** because that is the screen already used for all-time triage.

## Goals / Non-goals

**Goals**
- `wt topics --by <axis>` (e.g. `bucket`, `project`) — one all-time (or `--last N`) table
  with rows = resolved facet values + hours + share bars.
- Use `resolve_facets` (SPEC-0027) so inherited children roll into the parent bucket.
- Topics without a value for that axis keep their own base-topic name as the row key
  (same rule as `report --by`).

**Non-goals**
- Changing `wt report` day-scoped tables.
- `--json` on topics (separate from SPEC-0026 idea-workflow JSON).
- New command name (`wt buckets`); extend `topics`.
- Auto-defaulting `topics` to `--by bucket` (opt-in flag only).

## Decision

Add `--by TEXT` to `wt topics`. When set, after aggregating base-topic hours (existing
`--last` / all-time logic), regroup with the same semantics as `report._regroup` via
`resolve_facets`. Render columns: hours, share, `<axis>` (row label). Omit the per-topic
`facets` column in `--by` mode (redundant). Default `wt topics` (no `--by`) unchanged.

`--by` and `--unmapped` are mutually exclusive: `--unmapped` is about base topics lacking
any effective mapping; `--by` is an aggregate view — combining them errors with a clear
message.

## Design

### CLI

```bash
wt topics --by bucket
wt topics --by bucket --last 30
wt topics --by project          # if that axis exists in mappings
```

Shell completion: reuse `complete_by_axis` from report.

### Library

In `report.topics(cfg, last=None, unmapped=False, by=None)`:

1. Build `agg` base-topic → seconds (existing).
2. If `unmapped` and `by`: raise / ClickException.
3. If `by`: `agg = _regroup(agg, by, load_mappings(cfg))` then sort by hours.
4. Table: label column named `by` (or “topic” when not regrouping); no facets column when
   `by` is set.
5. Panel subtitle notes `· by {axis}`.
6. Keep the mappings.yaml summary panel as today (exact keys only — still useful).

### Tests

- Unit: with tmp mappings + monkeypatched agg (or thin helper), `--by bucket` merges
  `parent` + `parent:child` into one row.
- CLI smoke: `wt topics --by bucket` exits 0; `--by` + `--unmapped` fails.

## Alternatives considered

- **`wt report --all --by bucket`** — would require inventing all-time report mode and
  changing report’s day-loop UX; rejected in favor of extending topics.
- **Default topics to by-bucket** — too surprising; flag is enough.
- **Separate `wt buckets`** — unnecessary command sprawl.

## Acceptance criteria

- [x] `wt topics --by bucket` prints one row per effective bucket (hours + share), all-time by default.
- [x] Inherited `prefix:suffix` hours (SPEC-0027) are included in the parent bucket row.
- [x] `--last N` still applies before regrouping.
- [x] Without `--by`, output matches prior topics behavior (base topics + facets column).
- [x] `--by` with `--unmapped` errors clearly.
- [x] Help documents `--by`; completion works for common axes.
- [x] Automated tests + `uv run pytest` green.

## Test plan

- **Automated:** `tests/test_topics_by.py` — regroup merge + mutual exclusion + help + default facets column.
- **Manual:** `wt topics --by bucket` — Example ~74.6h, AI-workstreams ~32h; condensed vs plain `wt topics`.
- **Regression:** full pytest (263 passed); plain `wt topics` / `--unmapped` unchanged.

## Rollout / migration

Opt-in flag. No data migration. README one-liner optional.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; pytest green; manual check noted.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

_None — command is `wt topics --by`._
