---
id: SPEC-0058
title: "Export schemes loadable from the user config dir"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
source_idea: IDEA-071
milestone: "M3: idea→spec pipeline"
tags: [specs, export, adapters, config]
supersedes: []
---

## Context

Promoted from `IDEA-071`. `SPEC-0029` (`REMOVED-extended` export scheme) was designed and
accepted 2026-07-22 but never built — `wt spec schemes` still only lists `plain-md`,
`REMOVED`, `wt-native`. Its design calls for a new Python module vendored inside
`src/wt/export_schemes/` plus a template file baked into the wt package — every org-specific
scheme would require a code change and release of wt.

`SPEC-0016`'s declarative tier already avoids Python for simple schemes: `TemplateScheme`
(`src/wt/export_schemes/template_scheme.py`) loads every `.toml` under
`export_schemes/manifests/` at module-import time and registers a scheme per file. But that
directory is hardcoded to `Path(__file__).parent / "manifests"` — still inside the installed
wt package. Adding *any* scheme today means editing wt's own source tree.

Exploration established two facts that make this cheap:
- `paths.config_dir()` takes no `cfg` argument (pure env-var/XDG resolution), so the loader can
  glob a second directory at the same module-import point with no wiring changes elsewhere.
- `register(scheme)` is a plain dict assignment — last registration wins on a name collision —
  so loading built-ins first and the user dir second gives "user overrides built-in" for free.

Out of scope here (deliberately, per exploration): the real org-project template is
mostly static boilerplate with no `CanonicalSpec` source field to hang it on — extending
`TemplateScheme`'s manifest shape to express that is `IDEA-017`'s follow-on spec's job, not
this one's.

## Goals / Non-goals

**Goals**
- `TemplateScheme` manifests also load from a user config-dir location, with zero code changes
  to wt for a new declarative scheme.
- User manifests override a built-in of the same name (predictable last-wins precedence).
- `wt spec schemes` shows a scheme's origin (built-in vs user-config) for discoverability.

**Non-goals**
- Loading a `.py` code-plugin scheme from the config dir (arbitrary code execution from a
  config file is a real trust boundary; declarative-only for this spec).
- Extending `TemplateScheme`'s manifest schema with new section kinds (static/boilerplate
  text) — that's `IDEA-017`'s spec.
- Changing the built-in schemes (`plain-md`, `REMOVED`, `wt-native`) themselves.

## Decision

`template_scheme.py`'s existing manifest-loading loop also globs
`Path(paths.config_dir()) / "schemes" / "*.toml"` — after the built-in `manifests/` dir, so a
same-named user manifest naturally overrides a built-in via `register()`'s last-write-wins
semantics. No new precedence code, no `cfg` threading required.

## Design

- **Loader (`template_scheme.py`):** factor the existing `if _MANIFEST_DIR.exists(): for
  _path in sorted(_MANIFEST_DIR.glob("*.toml")): register(...)` into a small
  `_load_manifests_from(dir_path, *, origin)` helper that also stamps `origin` ("built-in" /
  "user-config") onto each `TemplateScheme` instance. Call it twice at module-import time: once
  for `_MANIFEST_DIR` (origin="built-in"), once for `Path(paths.config_dir()) / "schemes"`
  (origin="user-config") — the second call after the first, so user names win.
- **`TemplateScheme.__init__`:** accept and store `origin` (default `"built-in"` for
  callers/tests that don't pass one).
- **Discoverability (`cli.py` `spec schemes`):** print each scheme's origin when it isn't the
  default built-in tier (e.g. `REMOVED-extended  [user-config]  …`); built-ins print unchanged
  (no visual noise for the common case).
- **No changes** to `export_schemes/__init__.py`'s `register`/`get`/`available` — reuse as-is.

## Alternatives considered

- **Thread `config_dir` through `cfg` into the scheme loader** — rejected: `paths.config_dir()`
  is already `cfg`-independent, and the loader runs at module-import time (before any `cfg` is
  built), so threading `cfg` would require restructuring import order for no benefit.
- **Allow a `.py` code-plugin path in the config dir** — rejected for this spec: real trust
  boundary (arbitrary code execution from a dropped file); revisit only if a declarative
  manifest genuinely can't express a future scheme.
- **Explicit `--scheme-dir` CLI flag instead of a fixed config-dir location** — rejected:
  XDG config dir is already the established location for `config.yaml`/`mappings.yaml`; a
  `schemes/` subdirectory there is consistent and needs no new flag.

## Acceptance criteria

- [x] A `.toml` manifest dropped in `$WT_CONFIG_DIR/schemes/` (or the XDG default
      `~/.config/wt/schemes/`) is registered and appears in `wt spec schemes` — no wt code
      change needed.
- [x] A user manifest with the same `name` as a built-in scheme (e.g. `plain-md`) replaces it;
      `wt spec export` using that name renders the user's version.
- [x] `wt spec schemes` shows `[user-config]` (or similar) next to a user-loaded scheme;
      built-in scheme output is unchanged.
- [x] Absence of `$WT_CONFIG_DIR/schemes/` is not an error (no directory required to exist).
- [x] Existing built-in schemes (`plain-md`, `REMOVED`, `wt-native`) behave identically
      when no user manifest overrides them.

## Test plan

- **Automated tests** (`tests/test_export_schemes.py`, 4 new tests): `load_manifests_from` on
  a missing dir is a no-op; on a real dir it loads + stamps `origin="user-config"` (pure
  function, no registry touched); an integration test reloads `template_scheme` with
  `WT_CONFIG_DIR` monkeypatched, asserting a new scheme registers AND a same-named `plain-md`
  manifest overrides the built-in's `description`/`origin` (registry snapshotted + restored in
  a `finally`); a CLI test asserts `wt spec schemes` shows `\[user-config]` next to the user
  scheme and not next to `wt-native`.
- **Manual verification (performed):** real `wt` binary with `WT_CONFIG_DIR=<scratch>` and a
  `schemes/demo.toml` (copy of `plain-md.toml`, renamed) — `wt spec schemes` listed `demo
  [user-config]` alongside the three unchanged built-ins.
- **Regression guard:** full `uv run pytest` green (371); built-in schemes byte-identical when
  no user `schemes/` dir exists (default `WT_CONFIG_DIR`).

## Rollout / migration

1. Land the loader change + origin stamping + `wt spec schemes` display, with tests.
2. No data migration — purely additive; nothing existing changes shape.
3. `python3 tools/spec_lint.py --write-ledger`; `uv run pytest`.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).
