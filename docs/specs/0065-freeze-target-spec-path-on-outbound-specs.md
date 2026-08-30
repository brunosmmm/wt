---
id: SPEC-0065
title: "Freeze target_spec_path on outbound specs; _portable_dest_path prefers it"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-078
parent: SPEC-0064
milestone: "M4: cli ergonomics"
tags: [export, reliability]
---

## Context

Promoted from idea `IDEA-078` (SPEC-0065).

  :PROPERTIES:
  :ID: IDEA-078
  :EPIC: SPEC-0064
  :END:
** Summary
Child of epic `SPEC-0064`.

SPEC-0065 — Freeze `target_spec_path` on outbound specs; `_portable_dest_path` prefers it
** Open questions

** Log

## Goals / Non-goals

**Goals**
- Freeze the fully resolved absolute portable-spec destination path into the outbound spec's
  own frontmatter at scaffold time, alongside the existing `target_repo`.
- Make `_portable_dest_path()` — the single function `pull_status`, `pull_clock`, and the
  future sweep (SPEC-0067) all call — prefer that frozen value over live config.
- Preserve current behavior for outbound specs scaffolded before this lands (no frozen field
  present): fall back to today's live `outbox_targets`-derived resolution.

**Non-goals**
- Not backfilling `target_spec_path` onto already-existing outbound specs — they keep working
  via the fallback. A backfill command is a plausible future add-on (see SPEC-0064 Non-goals).
- Not changing the explicit `--to` override path on `pull-status`/`pull-clock` — an explicit
  `--to` still wins over both the frozen field and the live-config fallback, unchanged.

## Decision

Compute the destination path once, at `scaffold_outbound()` time (`specs.py`), using the exact
same `repo_path` + `spec_dir` + filename logic `_portable_dest_path()` already performs on every
call — but store the result as a new `target_spec_path` frontmatter field instead of
recomputing it from live config on every future read. `_portable_dest_path()` then reads that
frozen field first; live config resolution becomes the fallback path for specs that predate the
field.

## Design

- **`specs.py::scaffold_outbound()`, ~L372-378:** immediately after the existing
  `target_repo = _target_repo(cfg, project)` line, add:
  ```python
  target_cfg = (cfg.get("outbox_targets") or {}).get(project, {})
  spec_dir_rel = target_cfg.get("spec_dir", "docs/specs")
  target_spec_path = str(Path(target_repo).expanduser() / spec_dir_rel / spec_path.name)
  ```
  and append `f"target_spec_path: {target_spec_path}"` to the `extra` frontmatter list (same
  list that already carries `target_project`/`target_repo`/`source_idea`). `spec_path.name` is
  already computed a few lines above (`f"{proj_code}-{num}-{slug}.md"`) and is exactly the
  filename `_portable_dest_path()` uses today (`source_path.name`), so this mirrors the existing
  resolution precisely rather than inventing a new naming scheme.
- **`export.py::_portable_dest_path(cfg, source_path, fm, to=None)`:** reorder to:
  1. `to` explicit override (unchanged, still wins).
  2. `fm.get("target_spec_path")` — if present, `return Path(frozen).expanduser()` directly, no
     config lookup at all.
  3. Fallback: today's existing `target_project` → `outbox_targets[project]['repo_path']` +
     `spec_dir` derivation, for specs scaffolded before this field existed.
- No change needed to `pull_status`/`pull_clock`/`fit_log` themselves — they all go through
  `_portable_dest_path()`, so the fix is centralized in one function.

## Alternatives considered

- **Recompute from `target_repo` alone (already frozen) instead of adding a whole new field** —
  rejected: `spec_dir` is *also* live-config-derived (`target_cfg.get("spec_dir", ...)`) and can
  drift independently of `repo_path`; freezing only the repo half leaves the same class of bug
  for the spec_dir half. Freezing the fully-resolved path closes both gaps at once.
- **Re-derive the frozen path lazily on first `pull-status` call instead of at scaffold time** —
  rejected: scaffold time is when `target_repo`/`target_project` are already being computed and
  written; deferring adds a second code path that must reach the same answer, for no benefit.

## Acceptance criteria

- [x] A newly scaffolded outbound spec's frontmatter includes `target_spec_path` set to the
      resolved absolute path (`<repo_path>/<spec_dir>/<filename>`).
- [x] After scaffolding, changing `outbox_targets[project].repo_path` or `spec_dir` in
      `config.yaml` does not change what `pull-status`/`pull-clock` resolve for that spec.
- [x] An outbound spec scaffolded before this change (no `target_spec_path` field) still
      resolves correctly via the existing live-config fallback — zero regression.
- [x] An explicit `--to` passed to `pull-status`/`pull-clock` still overrides both the frozen
      field and the fallback, unchanged from today.

## Test plan

- **Automated tests:** `tests/test_specs.py` — `scaffold_outbound` writes `target_spec_path`
  matching `repo_path/spec_dir/filename`. `tests/test_export.py` — `_portable_dest_path` prefers
  the frozen field over `outbox_targets` when both are present and disagree (simulate a config
  change after export); falls back correctly when `target_spec_path` is absent from frontmatter
  (fixture built without it, mimicking a pre-existing outbound spec); `--to` still overrides
  both.
- **Manual verification:** scaffold a real scratch outbound spec, confirm `target_spec_path` in
  its frontmatter, then edit `~/.config/wt/config.yaml`'s `repo_path` for that project and
  confirm `wt spec pull-status <id>` still targets the original (frozen) location.
- **Regression guard:** full `uv run pytest` green; existing `pull-status`/`pull-clock`
  behavior for specs without the new field is byte-identical to before.

## Rollout / migration

1. Add `target_spec_path` computation + frontmatter write to `scaffold_outbound()`.
2. Update `_portable_dest_path()` to prefer the frozen field, with the live-config fallback
   preserved for pre-existing outbound specs.
3. No data migration needed — existing outbound specs simply keep using the fallback path
   until they're re-exported (or never, if never touched again); nothing forces a rewrite.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- None blocking.
