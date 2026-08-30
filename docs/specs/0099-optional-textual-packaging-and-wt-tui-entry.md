---
id: SPEC-0099
title: "Optional Textual packaging and wt tui entry"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
parent: SPEC-0098
milestone: "M5: interactive desk"
source_idea: IDEA-129
tags: [tui, packaging]
---

## Context

Child of [SPEC-0098](./0098-light-ideas-tui-beside-classic-cli.md) (IDEA-129). The desk needs
an opt-in Textual dependency and a Click entry point without changing the default `wt`
install or classic CLI behavior.

## Goals / Non-goals

**Goals**
- Declare Textual as an optional extra pinned `textual>=8,<9` (e.g. `[project.optional-dependencies] tui`).
- Add `wt tui` Click command that imports Textual and starts the app shell (placeholder /
  stub OK until SPEC-0100).
- If Textual is missing, exit non-zero with a clear install hint (`uv sync --extra tui` /
  equivalent).

**Non-goals**
- Desk UI behavior (SPEC-0100+).
- Making Textual a hard runtime dependency.
- Changing bare `wt` dashboard behavior.

## Decision

Package Textual only under optional extra `tui` with pin `textual>=8,<9`. Register
`@cli.command("tui")` in `cli.py` that lazy-imports the TUI module; when the extra is absent,
print install guidance and exit 1. Default `dependencies` and CI without the extra stay
unchanged.

## Design

**As shipped.**

- `pyproject.toml`: `[project.optional-dependencies] tui = ["textual>=8,<9"]` (resolved to
  `textual==8.2.8` locally). Hard deps untouched.
- `src/wt/tui/__init__.py`: no Textual import at module scope. Exports `INSTALL_HINT`,
  `MissingTextual`, `textual_available()` (an `importlib.util.find_spec` probe), and
  `run(cfg, **kwargs)`.
- **The guard probes, it does not catch.** `run()` checks `textual_available()` *before*
  importing `wt.tui.app`, rather than wrapping the import in `except ImportError`. Catching
  would let a real `ImportError` from a bug inside the app module masquerade as a missing
  dependency — there is a regression test for exactly that.
- `src/wt/tui/app.py`: imports Textual at module scope (only reachable via `run()`); holds
  `IdeaDesk(App)` — a placeholder `Static` + `Footer` with a `q` binding — and `run_app(cfg)`.
  SPEC-0100 replaces the body.
- `src/wt/cli.py`: `@cli.command("tui")` does a function-local `from . import tui as T`, calls
  `T.run(cfg)`, and converts `MissingTextual` into `click.ClickException` (exit 1). The module
  docstring's subcommand list gains a `tui` line.
- Docs: an "Optional interactive desk" section in `docs/WORKFLOW.md`.

## Alternatives considered

- **Hard-dep Textual** — rejected; agents/CI should stay light.
- **Rich Live pseudo-TUI** — rejected at epic level (painful input/focus).
- **`WT_TUI=1 wt`** — rejected; hidden; conflicts with default dashboard.

## Acceptance criteria

- [x] Optional extra declares `textual>=8,<9`.
- [x] `wt tui` exists; without Textual installed, exits with install hint (non-zero).
- [x] With Textual installed, `wt tui` starts without error (stub app acceptable).
- [x] Base install / `uv run pytest` without the extra still passes; no new hard deps.

## Test plan

**Executed 2026-07-30.**

- **Automated tests** — `tests/test_tui_entry.py` (6 tests):
  - `test_textual_is_an_optional_extra_not_a_hard_dep` — reads `pyproject.toml`; asserts the
    pin and that no hard dep mentions textual.
  - `test_cli_module_does_not_import_textual_or_the_tui_app` — subprocess imports `wt.cli` and
    asserts neither `textual` nor `wt.tui` is in `sys.modules`.
  - `test_run_raises_missing_textual_when_extra_absent` / `test_wt_tui_exits_nonzero_with_install_hint`
    — probe monkeypatched false → `MissingTextual`, and non-zero exit with the install hint.
  - `test_missing_dependency_guard_does_not_swallow_app_bugs` — an `ImportError` from inside
    the app module propagates as itself.
  - `test_app_shell_constructs_and_runs_headless` — Textual `run_test()` pilot; skipped when
    the extra is absent.
- **Manual verification** — without the extra, `uv run wt tui` printed the three-line install
  hint and exited 1. After `uv sync --extra tui` (textual 8.2.8), the app shell starts clean;
  verified headlessly via the pilot rather than an interactive attach (no TTY in this session).
- **Regression guard** — `uv run pytest`: **770 passed** with the extra installed; before
  installing it, the same suite was green with the pilot test skipped (5 passed / 1 skipped in
  the new file). `python3 tools/spec_lint.py` exits 0.

## Clock Log

`wt idea clock-in/out` on IDEA-129 (org LOGBOOK, not mirrored here).

## Rollout / migration

Land before SPEC-0100. No data migration.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none)
