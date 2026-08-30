---
id: SPEC-0137
title: "wt projects add: CLI register outbox targets (dry-run + --yes)"
status: done
owner: user
created: 2026-08-30
updated: 2026-08-30
source_idea: IDEA-293
kind: feature
milestone: "M4: cli ergonomics"
tags: [cli, projects, config, skills, ergonomics]
depends_on: [SPEC-0015, SPEC-0018, SPEC-0020, SPEC-0042, SPEC-0095]
---

## Context

Promoted from `IDEA-293`. Skills (`wt-orient`, `wt-seed`, `wt-explore`) implement the
[SPEC-0095](./0095-skill-cli-detect-multi-project-conversations-and.md) multi-project gate by
telling agents: never invent `outbox_targets` — ask the human to configure them. In practice
that meant hand-editing `~/.config/wt/config.yaml`. There was no CLI to register a project.

## Goals / Non-goals

**Goals**

- Promote `wt projects` to a Click group with default `list` (parity with `wt ideas`).
- `wt projects add NAME [--repo PATH] [--scheme S] [--spec-dir D] [--force] [--yes]`:
  dry-run plan by default; `--yes` commits to the user `config.yaml`.
- Association-only (no `--repo`) writes `outbox_targets[NAME]: {}`.
- Full target (`--repo`) sets `repo_path` (optional scheme / spec_dir).
- `outbound` in `wt.projects.v1` means non-empty usable `repo_path` (stub entries still listed).
- Skills + `docs/WORKFLOW.md` teach the CLI recipe instead of hand-editing YAML.
- Promote-error copy (SPEC-0020) points at `wt projects add … --yes`.

**Non-goals**

- Sheet / `idea_extensions` setup; interactive prompts; auto `wt map`; delete project;
  preserving YAML comments on round-trip.

## Decision

Single registry remains `outbox_targets`. Register via `wt projects add` with an explicit
`--yes` write gate. Skills forbid silent invention: show the dry-run plan, get agreement,
then `--yes`.

## Design

Shipped as decided:

- `ProjectsGroup` + `list` / `add` in `src/wt/cli.py`.
- `plan_project_add` / `apply_project_add` / `_outbound_flag` in `src/wt/rules.py`
  (backup `config.yaml.bak.<timestamp>`, atomic replace).
- `add --json` emits `wt.projects.add.v1`.
- Skills: `wt-orient`, `wt-seed`, `wt-explore`; `docs/WORKFLOW.md`; promote `ValueError` in
  `specs.promote_idea`.

## Acceptance criteria

- [x] `wt projects` / `wt projects --json` still work after the group migration.
- [x] `wt projects add NAME` (no `--yes`) prints a plan and does not modify `config.yaml`.
- [x] `wt projects add NAME --yes` creates `outbox_targets[NAME]: {}`; name appears in
      `--json` with `outbound: false`.
- [x] `wt projects add NAME --repo PATH --yes` sets `repo_path`; `--json` shows
      `outbound: true` and research root from that path when resolvable.
- [x] Missing repo path / conflicting `repo_path` fail without `--force`; succeed with
      `--force` as specified.
- [x] Skills + WORKFLOW describe the CLI recipe; no “hand-edit config.yaml” as the primary
      path for new projects.
- [x] Promote error for unconfigured project mentions `wt projects add`.
- [x] Focused tests pass; `python3 tools/spec_lint.py` exits 0.

## Test plan

Executed:

- **Automated:** `tests/test_projects_add.py` (plan/apply/CLI); `tests/test_projects_json.py`;
  `tests/test_assoc.py`; `tests/test_promote.py` — 49 passed.
- **Manual:** throwaway `WT_CONFIG_DIR` — dry-run unchanged file; `--yes` stub; `--repo` +
  `--json` outbound true; conflict error; `--force` overwrite.
- **Regression:** list/`--json` schema `wt.projects.v1` unchanged.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions on focused suite.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_(none)_
