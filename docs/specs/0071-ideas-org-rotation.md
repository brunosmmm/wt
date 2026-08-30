---
id: SPEC-0071
title: "Automatic ideas.org rotation past a line-count threshold"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-083
parent: SPEC-0070
milestone: "M4: cli ergonomics"
tags: [org, maintenance]
---

## Context

Promoted from idea `IDEA-083` (SPEC-0071).

  :PROPERTIES:
  :ID: IDEA-083
  :EPIC: SPEC-0070
  :END:
** Summary
Child of epic `SPEC-0070`.

SPEC-0071 — File-rotation primitive (`maybe_rotate_ideas_file`) wired into `add_idea`,
** Open questions

** Log

## Goals / Non-goals

**Goals**
- A new `org_write.py::maybe_rotate_ideas_file(cfg)` primitive: once `cfg['org_ideas_file']`
  crosses a configurable line-count threshold, atomically rename it to a dated historical file
  and write a fresh (header-only) file back at the *original* configured path.
- Wire it into `add_idea()` so rotation happens automatically on capture — no command to
  remember.
- Zero disruption to anything downstream: `load_tasks`'s existing recursive glob already picks
  up the renamed historical file with no code changes needed there.

**Non-goals**
- Not archiving/moving individual idea subtrees by state — that's SPEC-0072/0073's job.
  Rotation is purely "the whole file got too big," independent of what's inside it.
- Not making `cfg['org_ideas_file']` itself change — it stays a fixed, stable config value
  forever; rotation only ever moves content *out* of that path into a new file, never redirects
  where new captures land.
- Not deleting or compacting anything — rotation is a pure rename; nothing is lost or rewritten.

## Decision

Check the active ideas file's line count at the top of `add_idea()`, before its existing
bootstrap-if-missing check. If over threshold, rename it to a dated file
(`ideas-YYYYMMDD.org`, with a numeric suffix on same-day collision) via `os.replace` (atomic on
the same filesystem), then write a fresh file with just the `#+TODO` header back at the
original path — reusing the exact header-bootstrap logic `add_idea` already has for a
missing file.

## Design

- **New config key** (`config.py::DEFAULT_CONFIG`): `idea_rotation_max_lines: 1200` — chosen as
  a little below `ideas.org`'s current real size (1829 lines) so the feature actually exercises
  itself soon after shipping, without being so small it rotates on trivial line counts.
- **`org_write.py::maybe_rotate_ideas_file(cfg)`** (new):
  ```python
  def maybe_rotate_ideas_file(cfg):
      path = os.path.expanduser(cfg["org_ideas_file"])
      if not os.path.exists(path):
          return None
      max_lines = cfg.get("idea_rotation_max_lines", 1200)
      with open(path) as f:
          n_lines = sum(1 for _ in f)
      if n_lines <= max_lines:
          return None

      today = dt.datetime.now(cfg.get("_tz")).strftime("%Y%m%d")
      d = os.path.dirname(path)
      base = os.path.splitext(os.path.basename(path))[0]
      dest = os.path.join(d, f"{base}-{today}.org")
      suffix = 1
      while os.path.exists(dest):
          suffix += 1
          dest = os.path.join(d, f"{base}-{today}-{suffix}.org")
      os.replace(path, dest)

      keywords = cfg.get("org_idea_keywords") or [
          "IDEA", "INCUBATE", "SPECCED", "|", "PROMOTED", "EXPORTED", "DROPPED"]
      with open(path, "w") as f:
          f.write(f"#+TODO: {' '.join(keywords)}\n\n")
      return dest
  ```
- **`add_idea()` wiring:** call `maybe_rotate_ideas_file(cfg)` as its first line, before the
  existing `if not os.path.exists(path):` bootstrap check. If rotation fires, the path exists
  again immediately (freshly written), so the existing bootstrap check is naturally skipped —
  no double-header-write. If rotation doesn't fire (file missing, or under threshold), behavior
  is byte-identical to today.
- **No other code changes required** — `_iter_org_paths` already recursively globs the whole
  `org_files` directory, so a renamed `ideas-20260726.org` sitting alongside `ideas.org` is
  picked up automatically by every read path (`wt ideas`, `wt next`, ID numbering, etc.).

## Alternatives considered

- **Point `org_ideas_file` at a new path on rotation (mutate config)** — rejected: requires
  writing to `config.yaml` from inside a library call (surprising, and fragile if the user's
  config has comments/formatting `yaml.safe_dump` would clobber); keeping the configured path
  permanently stable and only ever moving old content *out* of it is simpler and has no such
  side effect.
- **Numeric rotation suffix (`ideas-002.org`) instead of a date** — rejected: a date is
  immediately meaningful to a human browsing the directory (mirrors the existing `journal/`
  convention already in this user's org setup) without needing to cross-reference anything.

## Acceptance criteria

- [x] A fixture ideas file with more lines than the configured threshold gets rotated on the
      next `add_idea` call: old content is preserved byte-for-byte under a new dated filename,
      and a fresh header-only file exists at the original path.
- [x] A fixture ideas file under the threshold is untouched — `add_idea` behaves identically to
      today.
- [x] After rotation, `wt ideas`/ID numbering still see ideas in the rotated historical file
      with no code changes needed on the read side.
- [x] `cfg['org_ideas_file']`'s configured value is never mutated by rotation.

## Test plan

- **Automated tests:** `tests/test_ideas.py` (shipped location) — `maybe_rotate_ideas_file`
  rotates a fixture file over threshold and leaves one under threshold untouched; two rotations
  on the same simulated day get distinct filenames (suffix collision handling); `add_idea`
  triggers rotation transparently and the new idea lands in the fresh file; the config path is
  never mutated; `load_tasks`/`next_idea_number` see ideas in both the active and rotated file
  with zero changes on that side (regression proof).
- **Manual verification:** temporarily lower `idea_rotation_max_lines` against a **copy** of
  the real `ideas.org`, capture one idea, confirm the rotation fires correctly, before ever
  running it against the real file live.
- **Regression guard:** full `uv run pytest` green; `add_idea` behavior for a file under
  threshold is byte-identical to before this spec.

## Rollout / migration

1. Add the config key + `maybe_rotate_ideas_file`, wire into `add_idea`.
2. No migration of the real `ideas.org` as part of this spec — it will rotate naturally the
   next time someone captures an idea after it's already over threshold (which, per the
   Summary's measurement, is true today — the very next real capture will exercise this for
   real).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- None blocking.
