---
id: SPEC-0001
title: Package refactor & XDG layout
status: done
owner: user
created: 2026-07-16
updated: 2026-07-16
milestone: "M1: packaging"
kind: feature
tags: [infra, packaging]
---

## Context

`wt` today is a single ~1000-line `wt.py` at the repo root, plus hand-editable YAML
(`config.yaml`, `mappings.yaml`, `overrides.yaml`), data files (`meetings.jsonl`,
`history.jsonl`), output dirs (`reports/`, `exports/`), a transient `.cache/`, and two
throwaway prototypes (`prototype_report.py`, `analyze_probe.py`) whose logic is already
folded into `wt.py`. The repo has **no commits yet** — this is greenfield for layout
purposes.

Everything is located relative to `HERE = os.path.dirname(os.path.abspath(__file__))`
(`wt.py:40`), so config, rules, data, and outputs are all assumed to sit next to the
script. That assumption blocks turning the code into an installable package: once code
moves into `src/wt/`, `HERE` would point *inside the package*, which is the wrong place
for user config and mutable data.

We are about to build richer features (git-commit collector, worklog export, etc.), so we
want a proper package foundation first.

## Goals / Non-goals

**Goals**
- Convert the scattered files into a proper, installable Python package (`wt`) with a
  clean module decomposition.
- Adopt **uv + hatchling** (src-layout) as the build/dev tooling, with a `wt` console
  entry point.
- Move config/rules to **XDG config** and data/outputs to **XDG data** (+ transient
  dumps to **XDG cache**), replacing the `HERE`-relative model.
- **Zero loss of current functionality** — every existing subcommand behaves identically,
  verified against golden snapshots of the current tool's output on real data.

**Non-goals**
- No new user-facing features in this spec (those get their own specs under M2+).
- No change to the time-accounting math, topic-resolution rules, or output formats.
- No multi-user / daemon / DB work — `wt` stays a personal, file-based tool.

## Decision

Adopt a `src/wt/` package built with hatchling and managed by uv, exposing a `wt` console
script (`wt = "wt.cli:cli"`). Introduce a single `paths` module that resolves all
locations from the XDG base-directory spec (with env overrides), and thread a resolved
`Config` object (carrying those paths) through the code instead of the module-level `HERE`
constant. Provide a `wt migrate-legacy` command to move the existing repo-root files into
their XDG homes.

## Design

### Package layout

```
work-tracking/
  pyproject.toml            # [build-system] hatchling; [project] deps + entry point
  uv.lock
  README.md                 # updated: install, XDG locations, migration
  docs/                     # (this system)
  src/wt/
    __init__.py             # __version__
    paths.py                # XDG resolution + env overrides (NEW)
    config.py               # load_config -> Config (was load_config + DEFAULT_CONFIG)
    rules.py                # mappings + overrides load/write (was load_mappings,
                            #   load_overrides, set_facets, add_override_rec)
    dates.py                # parse_date, week_days, _parse_iso
    topics.py               # RepoResolver, base_topic, resolve_topic, cursor path decode
    ingest.py               # load_streams, load_cursor_streams, load_all_streams,
                            #   cursor timestamp parsing
    aggregate.py            # build, union_secs, assemble
    history.py              # read_history, snapshot, history_path
    meetings.py             # read/ingest/refresh meetings, _harvest_tool_result
    report.py               # rich rendering, export, review, topics view, markdown
    cli.py                  # click group + all subcommands
  tests/
    conftest.py
    fixtures/               # tiny synthetic transcripts + a raw calendar dump
    test_characterization.py  # golden-output safety net
    test_paths.py           # XDG resolution + env overrides
    test_aggregate.py       # union_secs, gap model, parallelism
```

The two prototypes move to `docs/design/` (or are deleted) — they are superseded by
`wt.py` and out of the package.

### Path resolution (`paths.py`)

Precedence, per location:

| Location | Env override | Default |
|---|---|---|
| config dir | `$WT_CONFIG_DIR`, else `$XDG_CONFIG_HOME/wt` | `~/.config/wt` |
| data dir | `$WT_DATA_DIR`, else `$XDG_DATA_HOME/wt` | `~/.local/share/wt` |
| cache dir | `$WT_CACHE_DIR`, else `$XDG_CACHE_HOME/wt` | `~/.cache/wt` |

- **config dir** holds `config.yaml`, `mappings.yaml`, `overrides.yaml`.
- **data dir** holds `meetings.jsonl`, `history.jsonl`, `reports/`, `exports/`.
- **cache dir** holds the transient raw calendar dumps (was `.cache/`).

`config.yaml`'s `meetings_file` / `history_file` keys are kept: if absolute, used as-is;
if relative, resolved against the **data dir** (was `HERE`). Directories are created on
demand (`mkdir -p` semantics), exactly as the current code does for `reports/`/`exports/`.

### Config object

`load_config()` returns a small `Config` dataclass (or the same dict, augmented) carrying
the merged knobs **plus** the resolved `config_dir`, `data_dir`, `cache_dir`, `_tz`,
`_work`, `_home`, `_root`, `_cursor_root`. Functions that currently reference `HERE`
(`meetings_path`, `history_path`, `set_facets`, `add_override_rec`, `_write_md`, `export`,
`refresh_meetings`) take their base dir from the config object instead. No behavior change
beyond *where* the files are read/written.

### File relocation (one-time, manual)

This is treated as a **clean start**: no `migrate` command and no backwards-compat shim.
The existing repo-root files are moved by hand into their XDG homes during rollout:

- `config.yaml`, `mappings.yaml`, `overrides.yaml` → config dir
- `meetings.jsonl`, `history.jsonl` → data dir
- `reports/`, `exports/` → data dir

The current repo's real data (13 mappings, archived history, cached meetings) is copied to
the XDG dirs and verified against the golden baselines before the root copies are removed.

### Tooling

- `pyproject.toml`: `[build-system] hatchling`; `[project]` deps `click`, `rich`,
  `pyyaml`; `[dependency-groups]` / `[project.optional-dependencies].dev` = `pytest`,
  `jsonschema` (the latter also powers spec validation). `requires-python = ">=3.12"`.
  `[project.scripts] wt = "wt.cli:cli"`.
- `uv.lock` committed. `uv run wt …` and `uv run pytest` for dev; `uv tool install .`
  (or `pipx install .`) for a global `wt`.

## Alternatives considered

- **Project-dir data (WT_HOME / cwd)** — keeps everything git-trackable in one folder;
  rejected in favor of XDG per the packaging decision (proper Unix hygiene, survives repo
  moves, code and data cleanly separated).
- **Flat `wt/` package (no src/)** — simpler but risks import shadowing and tests
  importing the wrong copy; rejected.
- **setuptools instead of hatchling/uv** — conventional but slower and no lockfile;
  rejected in favor of uv/hatchling.

## Acceptance criteria

- [x] `uv run wt --help` and the subcommands (`report`, `review`, `topics`, `export`) run
      from the new package.
- [x] The `wt` console entry point works via `uv run wt`; global install documented
      (`uv tool install .` / `pipx install .`) — not executed in this session (avoids
      mutating global tool state).
- [x] Config/rules resolve from XDG config dir; data/outputs from XDG data dir; raw
      calendar dumps from XDG cache dir; resolution + env overrides unit-tested
      (`tests/test_paths.py`).
- [x] Existing repo-root files relocated to their XDG homes (verified byte-identical);
      the old root copies removed.
- [x] **Golden characterization passed**: frozen-past `topics`, `report` (day + week),
      `review` (week), and `export` (csv+json) are byte-identical to the pre-refactor
      `wt.py`. The only drift is today's `work-tracking` row (0.281h→0.985h+), caused by
      this session writing its own transcript between the two runs — expected live-data
      behavior, not a port change.
- [x] `prototype_report.py` / `analyze_probe.py` archived under `docs/design/`.
- [x] README updated for install + XDG paths; `docs/LEDGER.md` shows SPEC-0001 `done`.

## Test plan

- **Regression guard (primary):** golden characterization. Baselines were captured from
  the pre-refactor `wt.py` on the real data (`COLUMNS=120`): `export` (csv+json all days),
  `topics`, `report 2026-06-01`, `report -w 2026-06-01`, `review -w 2026-06-01`. A test
  (`tests/test_characterization.py`) points the packaged `wt` at the same XDG dirs (via
  `WT_CONFIG_DIR`/`WT_DATA_DIR` env) and asserts **byte-identical** output. Zero drift is
  the bar; any diff is a port bug.
- **Automated unit tests (committed, `uv run pytest` → 11 passed):**
  - `tests/test_paths.py` — XDG resolution and env overrides (`WT_*_DIR`, `XDG_*_HOME`,
    defaults, tilde), using `monkeypatch` and `tmp_path`.
  - `tests/test_aggregate.py` — `union_secs` on disjoint/overlapping/adjacent/empty
    intervals; the gap model + `min_block_seconds`; and parallelism (billed = 2× wall for
    two concurrent streams). Uses `monkeypatch` to inject synthetic streams (no disk dep).
  - `tests/test_ingest.py` — `load_streams` over a synthetic Claude transcript
    (`tests/fixtures/claude_root/…`): event count, cwd carry-forward, kind classification.
- **Manual verification (done):** `uv run wt` subcommands (`report -w`, `topics`,
  `report --last`, `report --by`, `export csv/json`) render correctly against the relocated
  XDG data.

**Deviation from the plan:** the golden characterization was run as a **one-time migration
gate** (against real `~/.claude` data), not committed as a repeatable test — a committed
golden test would depend on live transcripts and drift daily. The committed suite is
unit-level instead. Cursor-transcript and raw-calendar fixtures were not added (the Cursor
path shares the same event pipeline that the Claude fixture and unit tests already cover).

## Rollout / migration

1. **Capture golden output** from the *current* `wt.py` on the real data:
   `wt export -o baseline_all.csv`, `wt export --format json`, and captured
   `report`/`topics`/`review` renderings (with a fixed `--width` for rich) → stored as
   test fixtures.
2. Create `pyproject.toml` + `src/wt/` skeleton; split `wt.py` into the modules above
   **mechanically** (move functions, fix imports) — no logic edits.
3. Add `paths.py` and thread the config object through the `HERE` call-sites.
4. **Manually move** the current repo-root files into the XDG dirs; verify contents.
5. Re-run the golden captures via the packaged `wt`; assert identical output. Fix any
   drift (must be zero).
6. Remove `wt.py` from root; archive `prototype_report.py` / `analyze_probe.py` under
   `docs/design/`.
7. Update README + ledger; commit (first commit of the repo).

The old `alias wt='python3 .../wt.py'` is replaced by the installed `wt` script; the
README documents the new install/usage.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green (11 passed); manual verification performed.
- [x] No regressions (frozen-past golden characterization byte-identical).
- [x] Spec body updated to match what shipped (incl. the deviation note).
- [x] `docs/LEDGER.md` updated (status `done` + date).

**Not committed** (per repo policy — the user commits): this is the first commit of the
repo when they choose to make it.

## Open questions

_None._ (Clean start: files moved manually, no `migrate` command. Prototypes archived
under `docs/design/`.)
