---
id: SPEC-0021
title: Relocate the outbound outbox to the wt data dir
status: done
owner: user
created: 2026-07-18
updated: 2026-07-18
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [specs, export, packaging]
depends_on: [SPEC-0015]
---

## Context

[SPEC-0015](./0015-outbound-spec-export.md) defaulted the outbound spec store (`outbox_dir`) to
`docs/outbox/` **inside the wt repo**. "Parallel namespace" kept outbound specs out of wt's
*ledger*, but they still landed in wt's *source tree* — so specs authxxed for **other projects**
get committed into the tool's own git history. That's wrong: the wt repo is the tool; outbound
specs are user content for other repos.

This revises SPEC-0015's outbox **location** decision only (the rest of SPEC-0015 stands).

## Goals / Non-goals

**Goals**
- Default `outbox_dir` to **`<data_dir>/outbox`** (e.g. `~/.local/share/wt/outbox/`), alongside
  the other user data wt owns (`mappings.yaml` is config; `history.jsonl`, `org-backups` are
  data). Nothing outbound ever touches wt's source tree.
- Remove `docs/outbox/` (README + INDEX) from the wt repo.
- Migrate any existing `docs/outbox/` content to the new location.

**Non-goals**
- Changing outbound authxxing/export/index/provenance behavior — only the base directory moves.
- Moving internal specs (`docs/specs/`) — those are genuinely wt's own governance and stay.

## Decision

`outbox_dir(cfg)` defaults to `Path(cfg["data_dir"]) / "outbox"` instead of
`Path.cwd() / "docs/outbox"`. Everything else (per-project subdirs, `<PROJ>-NNNN` ids,
`INDEX.md`, `PROVENANCE.md`, `scaffold_outbound`, `export_spec`) is unchanged — it just roots
under the data dir. `docs/outbox/` is deleted from the repo. `wt spec export` still drops the
real, version-controlled copy into the **target repo** (SPEC-0015/0016 unchanged).

## Design

- `src/wt/specs.py:outbox_dir` → `Path(cfg.get("outbox_dir") or (Path(cfg["data_dir"]) /
  "outbox"))`. (Tests already inject `cfg["outbox_dir"]` at a tmp path, so they're unaffected;
  the change is only the *default*.)
- Update the module docstring + any `docs/outbox` references.
- Repo cleanup: `git rm -r docs/outbox/` (README.md + INDEX.md).
- Migration (one-time, for the current machine): move any existing
  `docs/outbox/<project>/…` drafts to `<data_dir>/outbox/<project>/…` and regenerate the index
  there. (Applies to the just-created `DEMO-0001` draft.)

## Alternatives considered

- **Keep it in the repo but `.gitignore` it** — rejected; a build artifact dir the tool writes
  into its own checkout is still wrong, and breaks a non-repo/installed usage.
- **Authxx straight into the target repo, no wt copy** — considered; rejected (user decision) in
  favor of a data-dir working area + provenance, so you get a cross-session draft + an outbound
  list without a target commit per edit.

## Acceptance criteria

- [x] With no `outbox_dir` override, `outbox_dir(cfg)` resolves under `cfg["data_dir"]`
      (`<data_dir>/outbox`), **not** the repo/cwd.
- [x] `docs/outbox/` is gone from the wt repo (untracked + removed from history going forward).
- [x] `wt spec new --target …`/`--from-idea …` (outbound) and `wt spec export` write under the
      data dir; nothing appears in the wt working tree.
- [x] The existing `DEMO-0001` draft is migrated to `<data_dir>/outbox/` (not lost).

## Test plan

- **Automated:** a test asserts `specs.outbox_dir({"data_dir": "/x"})` == `/x/outbox` (default
  now roots at data_dir); existing `tests/test_export.py`/`test_routing.py` (which inject a tmp
  `outbox_dir`) stay green. A guard asserts the default is not under `docs/`.
- **Manual verification:** `wt spec new --from-idea IDEA-001` (outbound) creates the spec under
  `~/.local/share/wt/outbox/`, and `git status` in the wt repo shows nothing new.
- **Regression guard:** `uv run pytest` green; `python3 tools/spec_lint.py` unaffected.

## Rollout / migration

1. Change the `outbox_dir` default + docstring.
2. `git rm -r docs/outbox/`; migrate existing drafts to `<data_dir>/outbox/`.
3. Add a cross-reference note to SPEC-0015 (location revised here; SPEC-0015 stays `done`).
4. Tests + manual; close the loop.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 206 passed; default-location test in test_export.py); manual: draft migrated to ~/.local/share/wt/outbox, repo clean of docs/outbox.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
