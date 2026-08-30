---
id: SPEC-0031
title: Rename idea explore to log; datetime Log stamps
status: done
owner: user
created: 2026-07-23
updated: 2026-07-23
milestone: "M4: cli ergonomics"
kind: feature
tags: [ideas, cli, ergonomics, explore]
source_idea: IDEA-019
depends_on: [SPEC-0024, SPEC-0030]
---

## Context

Promoted from idea `IDEA-019`.

[SPEC-0024](./0024-formal-explore-stage-wt-explore-skill.md) named the CLI verb
`wt idea explore` for appending a Log entry. That verb oversells the CLI: exploration
is what the agent does (`/wt-explore`); the CLI only logs a finding (and may move
`IDEA` → `INCUBATE`). Help text already says “Append a dated Log entry.”

Separately, Log headlines are date-only (`*** YYYY-MM-DD`), so multiple notes in one
session collide visually and lose ordering within the day.

## Goals / Non-goals

**Goals**
- Primary CLI verb: `wt idea log <selector> --note "…"`.
- Keep `explore` as a **hidden Click alias** of `log` for one release (no help listing);
  same behavior.
- Update `next_step_for_idea`, promote-empty-Summary warn, WORKFLOW, and skills to prefer
  `wt idea log`.
- Log entry headlines use date **and** time: `*** YYYY-MM-DD HH:MM` in `cfg["_tz"]`.
- Stage name / skill `/wt-explore` unchanged (still the enrichment playbook).

**Non-goals**
- Renaming the org `** Log` section or `INCUBATE` state.
- Full org active timestamps (`<…>`).
- Removing the `explore` alias in this change (defer to a later cleanup).
- Changing Summary/questions commands.

## Decision

Rename the user-facing command to `log`; alias `explore`; stamp Log heads with
`YYYY-MM-DD HH:MM` local to the configured timezone.

## Design

### CLI (`src/wt/cli.py`)

```python
@idea_group.command("log")
@click.command("explore", hidden=True)  # or click alias pattern used in-repo
```

Prefer Click’s `context_settings` / secondary name if the codebase already has a pattern;
otherwise register `log` as the real command and a thin hidden `explore` that calls the
same callback. Help examples and `IdeaGroup` docstring show `log` only.

### Library

`append_log(..., when=None)` default:

```python
dt.datetime.now(cfg.get("_tz")).strftime("%Y-%m-%d %H:%M")
```

Explicit `when=` still accepted (tests may pass a fixed string). Existing date-only
headlines in old ideas are left as-is (no migration).

### Hints / docs / skills

- `workflow.next_step_for_idea`: empty Summary → `wt idea log {id}`.
- `specs.scaffold_*` empty-Summary warn: mention `wt idea log` / `/wt-explore`.
- `docs/WORKFLOW.md`, `skills/wt-explore`, `wt-seed`, `wt-capture`, `wt-orient`: say
  `wt idea log` for appending notes; keep “explore stage” / `/wt-explore` naming.

### Tests

Update assertions that expect `wt idea explore` in next-hints; add a test that a new log
headline matches `\d{4}-\d{2}-\d{2} \d{2}:\d{2}`; CLI `wt idea log …` works; hidden
`explore` still works.

## Alternatives considered

- **Keep CLI name `explore`** — rejected; mismatches what the command does.
- **Rename skill to wt-log** — rejected; the skill still orchestrates exploration, not
  merely logging.
- **Hard-delete `explore` immediately** — harsher than needed; hidden alias is cheap.
- **Seconds in the stamp** — unnecessary noise for human Log browsing.

## Acceptance criteria

- [x] `wt idea log ID --note "…"` appends a Log entry and is the documented primary verb.
- [x] `wt idea explore …` still works (hidden alias).
- [x] New Log headlines are `*** YYYY-MM-DD HH:MM` in the configured timezone.
- [x] `wt next` / empty-Summary path suggests `wt idea log …`.
- [x] Skills + WORKFLOW prefer `log` for the CLI; `/wt-explore` name unchanged.
- [x] Tests + full pytest green.

## Test plan

- **Automated:** `tests/test_workflow.py`, `tests/test_explore.py` — datetime stamp; `log` +
  hidden `explore` alias; next-hints say `log`.
- **Manual:** `wt idea log IDEA-019 --note "datetime stamp check after SPEC-0031"` →
  `*** 2026-07-23 07:42`; `wt idea --help` lists `log`, not `explore`.
- **Regression:** `uv run pytest` green after ledger refresh.

## Rollout / migration

Ship alias. No org data rewrite. Later spec may drop the alias once habits move.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; pytest green; manual check noted.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

_None — hard-rename deferred via hidden alias; time format locked to `YYYY-MM-DD HH:MM`._
