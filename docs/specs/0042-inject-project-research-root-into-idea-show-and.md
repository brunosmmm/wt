---
id: SPEC-0042
title: "Inject project research root into idea show and wt-explore"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
tags: [skills, explore, cli, ergonomics]
source_idea: IDEA-047
depends_on: [SPEC-0024, SPEC-0026, SPEC-0015, SPEC-0020]
---

## Context

Promoted from `IDEA-047`. `/wt-explore` told agents to research code/docs but not **which
tree**. Outbound ideas carry `:PROJECT:` and `outbox_targets[project].repo_path` already
names that tree — yet `wt idea show` only exposed `project`.

**Meta-Tools** is **internal**: research root is this wt checkout (no `outbox_targets` entry).

## Goals / Non-goals

**Goals**
- Resolve a research root from an idea’s `:PROJECT:` using existing config (no new path map).
- Expose it on `wt idea show` (plain + `--json`).
- Update `wt-explore` / `wt-new-work` to require using that root when set.

**Non-goals**
- A `research_roots` config knob.
- A separate explore-context subcommand.
- Changing promote/export routing.

## Decision

`resolve_research_context(cfg, project)` prefers `outbox_targets[project].repo_path`; for
**Meta-Tools**, discovers this wt repo; otherwise null + note. Idea show carries a `research`
block; skills must use it.

## Design

### Resolver (`wt.rules`)

- `discover_wt_checkout()` — walk from the `wt` package to `src/wt` + `pyproject.toml`.
- `resolve_research_context(cfg, project)`:
  - project ∈ `outbox_targets` → expanded `repo_path`, `source: outbox_targets`, optional
    `spec_dir` / `scheme`
  - `Meta-Tools` → discovered checkout, `source: internal`
  - other / missing → `root: null`, `source: none`, actionable `note`

### Idea show (`wt.explore`)

- `idea_show_payload` always includes `research`.
- Plain show: `research: <path> (<source>)` or `research: (none) — <note>`.

### Skills / docs

- `wt-explore`: after show, analyze `research.root` first when set.
- `wt-new-work`: resolve before authxxing.
- `WORKFLOW.md`: outbox path is also the explore research root; Meta-Tools = this repo.

## Alternatives considered

- **`research_roots` map** — rejected.
- **Skill-only** — rejected; need machine field on show.
- **Meta-Tools in outbox_targets** — rejected (would force outbound promote).

## Acceptance criteria

- [x] Outbound projects resolve via `outbox_targets.repo_path` (+ spec_dir/scheme).
- [x] `Meta-Tools` → this wt checkout (`source: internal`).
- [x] Unconfigured project → null root + note (no guessed path).
- [x] `wt idea show --json` / plain include `research`.
- [x] `wt-explore` / `wt-new-work` skills updated.
- [x] No new research-roots config key.

## Test plan

- **Automated:** `tests/test_research_context.py` + `test_json_cli` research assert.
  `uv run pytest` green.
- **Manual:** IDEA-047 → internal wt root; IDEA-046 → `~/work/demo-project`.
- **Regression:** promote/export unchanged.

## Rollout / migration

None — existing `outbox_targets` unlock explore routing immediately.

## Definition of done

- [x] AC met; tests green; ledger current; body matches shipped.

## Open questions

_None._
