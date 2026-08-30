---
id: SPEC-0020
title: Project-aware promotion routing
status: done
owner: user
created: 2026-07-18
updated: 2026-07-18
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [cli, ideas, specs, export]
depends_on: [SPEC-0013, SPEC-0015, SPEC-0018]
---

## Context

`wt spec new --from-idea <sel>` **always** mints an internal `SPEC-NNNN` in `docs/specs/`,
ignoring the idea's `:PROJECT:` association ([SPEC-0018](./0018-capture-entity-association.md)).
So an idea explicitly tied to another project (e.g. `AI-workstreams`) silently landed in `wt`'s
**own** governance namespace + ledger — violating the internal/outbound separation locked in
for [SPEC-0011](./0011-idea-to-spec-pipeline.md)/[SPEC-0015](./0015-outbound-spec-export.md).
(This actually happened: `IDEA-001` → a bogus internal `SPEC-0020`, since reverted.) The only
way to get an outbound spec today is to *also* pass `--target`, which is redundant with what the
idea already declares.

## Goals / Non-goals

**Goals**
- `wt spec new --from-idea` **routes by the idea's project**: a project that maps to a configured
  outbound target promotes into that target's outbound namespace (`<PROJ>-NNNN` under
  `docs/outbox/`), never an internal `SPEC-NNNN`.
- An idea with **no** project (or `--internal`) promotes to an internal `SPEC-NNNN` (genuine wt
  work). `--target X` overrides the routing target.
- A project with **no configured outbound target** → promotion **stops with a clear error**
  telling you how to configure it (never silently mints an internal id).

**Non-goals**
- Auto-creating/guessing a target repo path (the error requires you to set it — user decision).
- Changing the outbound spec format/scheme (that's SPEC-0015/0016).
- Routing by anything other than the `:PROJECT:` association (+ explicit flags).

## Decision

Insert a routing decision in front of scaffolding. `wt spec new --from-idea` resolves the
idea's target project (from `--target`, else `:PROJECT:`), then:
- `--internal` (or no project and no `--target`) → `scaffold_from_idea` (internal `SPEC-NNNN`).
- project ∈ `outbox_targets` → `scaffold_outbound(cfg, project, from_idea=…)` (outbound namespace).
- project ∉ `outbox_targets` → **error**: name the project + how to configure its target.

The idea↔spec link, `source_idea`, and `IDEA→SPECCED` transition happen the same way in either
branch (internal or outbound), so the reciprocal `:SPEC:` on the idea points at whichever id was
actually created.

## Design

### Routing (`src/wt/specs.py`)

- `promote_idea(cfg, selector, *, internal=False, target=None, epic=False, title=None,
  force=False) -> (path, spec_id, kind)` where `kind ∈ {"internal","outbound"}`:
  1. `task = resolve_selector(cfg, selector)`; must be an idea; honor the existing
     already-promoted guard (`:SPEC:` present ⇒ error unless `force`).
  2. `project = target or task.properties.get("PROJECT")`.
  3. If `internal` **or** `project is None` → `scaffold_from_idea(...)` (internal).
  4. Elif `project in cfg.get("outbox_targets", {})` → `scaffold_outbound(cfg, project,
     from_idea=selector, title=title)` (outbound; already sets the reciprocal `:SPEC:` +
     `IDEA→SPECCED` per SPEC-0015).
  5. Else → `raise ValueError` with a message like: *"idea IDEA-001 is associated with project
     'AI-workstreams', which has no outbound target. Configure `outbox_targets['AI-workstreams']
     .repo_path` in config.yaml, or pass `--target <proj>` / `--internal`."*
- Keep `scaffold_from_idea` and `scaffold_outbound` as-is; `promote_idea` only *dispatches*.
  (`--epic` still applies to the internal branch.)

### CLI (`src/wt/cli.py`)

- `wt spec new --from-idea <sel>` calls `promote_idea`. Add `--internal` (force internal);
  `--target` already exists. The success line reports the created id + whether it's internal or
  `outbound → <repo>`.
- `--target` **without** `--from-idea` keeps working (scaffold a blank outbound spec), unchanged.

### Config

No new keys — reuse `outbox_targets` (SPEC-0015) as the project→repo registry. A target entry
gains meaning as "this project's ideas promote here." (Populating it is the user's setup step,
surfaced by the error.)

## Alternatives considered

- **Keep internal-by-default, require `--target`** — rejected; it's the current footgun and
  ignores the association the idea already carries.
- **Warn + fall back to internal when unconfigured** — rejected (user decision); silent internal
  ids for other-repo work is exactly the bug. Stop-and-require-setup is explicit.
- **Auto-create the target from the bucket→repo mapping** — deferred; a bucket can span several
  repos, so the target repo is a deliberate config choice, not inferable.

## Acceptance criteria

- [x] `wt spec new --from-idea <idea-with-project-that-has-a-target>` creates an **outbound**
      spec (`<PROJ>-NNNN` under `docs/outbox/`, not `docs/specs/`), links it, and flips the idea
      to `SPECCED` with a `:SPEC:` pointing at the outbound id.
- [x] `wt spec new --from-idea <idea-with-no-project>` (or `--internal`) creates an internal
      `SPEC-NNNN` as before.
- [x] `wt spec new --from-idea <idea-with-project-but-no-target>` **errors** without writing any
      spec or mutating the idea, naming the project + the fix.
- [x] `--target X` overrides the routing target; `--internal` forces internal even with a project.
- [x] `docs/specs`/`tools/spec_lint.py` never receive an other-repo idea's spec.

## Test plan

- **Automated:** `tests/test_routing.py` (tmp org + tmp specs/outbox dirs): idea with project in
  `outbox_targets` → `promote_idea` returns `("…","<PROJ>-NNNN","outbound")`, file under the
  outbox, `:SPEC:`/`SPECCED` set; idea with no project → internal `SPEC-NNNN`; idea with project
  absent from `outbox_targets` → `ValueError` **and** no file created + idea unchanged (state
  still `IDEA`, no `:SPEC:`); `--internal` and `--target` overrides; CLI via `CliRunner`
  (success lines + the error path exit code/message).
- **Manual verification:** configure `outbox_targets['AI-workstreams'].repo_path`, then
  `wt spec new --from-idea IDEA-001` → outbound spec in the outbox (tmp); without the config →
  the setup error.
- **Regression guard:** `uv run pytest` green; SPEC-0013 internal promotion + SPEC-0015 outbound
  scaffolding unchanged when reached through the dispatcher.

## Rollout / migration

1. `promote_idea` dispatcher in `specs.py`.
2. `wt spec new` wires to it; add `--internal`; enrich the success/error output.
3. Tests + manual; close the loop.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 202 passed; `tests/test_routing.py`); manual verification by the verifier (outbound route → DEMO-0001 under outbox; internal route; error path leaves idea IDEA/None + no leaked file).
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._

## What shipped

Implemented as designed: `specs.promote_idea(cfg, selector, *, internal=False, target=None,
epic=False, title=None, force=False) -> (path, spec_id, kind)` dispatches to
`scaffold_from_idea` (kind `"internal"`) or `scaffold_outbound` (kind `"outbound"`), or raises
`ValueError` (naming the project + fix) before either scaffolder runs — no file written, idea
untouched. `wt spec new` gained `--internal`; the success line now reports `internal` or
`outbound → <repo>`. `scaffold_from_idea`/`scaffold_outbound` were not modified. Automated
coverage in `tests/test_routing.py` (10 cases: outbound/internal/target-override/`--internal`
override/already-promoted-guard/error-without-mutation, plus CLI via `CliRunner`); manual
verification exercised all three routes in a tmp workspace outside the repo. `uv run pytest`
(202 passed) and `python3 tools/spec_lint.py` (21 specs OK) both green.
