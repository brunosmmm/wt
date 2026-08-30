---
id: SPEC-0016
title: Pluggable export schemes + REMOVED adapter
status: done
owner: user
created: 2026-07-16
updated: 2026-07-18
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [specs, export, adapters]
parent: SPEC-0011
depends_on: [SPEC-0015]
---

## Context

[SPEC-0015](./0015-outbound-spec-export.md) exports outbound specs by file-drop in `wt`'s own
(`wt-native`) shape. But different downstream consumers ingest **different spec shapes**. A
concrete example is REMOVED (`sdlcbundle-REMOVED`, a multi-agent SDLC
pipeline): its unit of work is a task keyed `X.Y.Z`, and it ingests (a) free-form spec
baselines in a repo's `specs/`, (b) a hierarchical `project-plan.md` (`### Deliverable X.Y` /
`#### X.Y.Z — Title` with bolded fields: `Outcome / Deliverable`, `Details and specific hints`,
`Dependencies`, `Verification`, `Do`, `Don't`, `Test bar`; deliverable-level `Objective`,
`Normative references`, `Primary scope paths`, `Key interfaces / contracts`, `Critical
constraints`), and (c) per-task specs at `specs/tasks/<task-id>-<slug>.md` following its
`task-spec-template.md` (Context · Requirements[Functional/Non-Functional] · Technical
Approach · Acceptance Criteria[binary checkboxes] · **Verification Steps**[exact build/unit/
integration/manual commands] · Dependencies · Out of Scope).

**Assessment — are our specs sufficient?** Content-wise mostly (we have Context, binary
Acceptance criteria, `depends_on`, Non-goals→Out of Scope, Decision+Design→Technical
Approach, Test plan→Verification). Shape-wise **no**: different granularity (`SPEC-NNNN` vs
`X.Y.Z`), different section names, and missing fields (Requirements F/NF split, command-form
Verification Steps, Outcome/Do/Don't/Test bar/scope paths). Critically, REMOVED is
**skeleton-tolerant**: `REMOVED` emits a task-spec skeleton with `<!-- PM: … -->`
markers and its PM role *refines* it — so an export only needs to be a well-formed **seed** in
the target's shape, not a complete spec.

Conclusion: keep `wt-native` as the default; add a **pluggable scheme layer** so the exporter
can render outbound specs into other consumers' shapes, `REMOVED` being the first.

## Goals / Non-goals

**Goals**
- A scheme/adapter abstraction the SPEC-0015 exporter delegates to; `wt-native` is the default
  scheme (the current behavior, refactored behind the seam).
- Scheme selection via `wt spec export --scheme <name>` and a per-target
  `outbox_targets[<project>].scheme` default; `wt spec schemes` lists available schemes.
- A `REMOVED` scheme that renders an outbound spec into REMOVED's shape (task-spec
  seed at `specs/tasks/<id>-<slug>.md`, optional `project-plan.md` fragment for an epic), with
  `<!-- fill -->` markers where `wt` lacks data.
- Two authxxing tiers: **declarative** schemes (a manifest: section map + naming + id format +
  body template) and **code-plugin** schemes (for real decomposition logic).

**Non-goals**
- Completing every downstream field (their PM refines skeletons; we emit faithful seeds).
- **Emitting architecture / codebase / design / style-guide baseline docs.** REMOVED's
  **Codebase Analyst** generates the architecture doc (`current-architecture-pre-task-X.Y.Z.md`)
  from the *target repo itself*, and style guides live in that repo — `wt` neither has that
  information nor should guess at it. We emit only the product-intent + decomposition layer.
- Overwriting anything already in the target repo (export is additive/non-clobbering, below).
- Round-tripping/importing a foreign spec back into `wt`.
- Live orchestration with REMOVED (still file-drop, per SPEC-0011/0015).

## Decision

Introduce an `ExportScheme` interface and a registry. `wt spec export` resolves a scheme
(CLI `--scheme` > target config > `wt-native`), validates the spec against the scheme's
`required_fields`, and writes the scheme's rendered `OutputFile`s into the target repo (reusing
SPEC-0015's atomic file-drop + provenance). Simple schemes are expressed as a **declarative
manifest**; schemes needing logic (like `REMOVED`'s `SPEC → X.Y.Z` decomposition) are
Python plugins. `REMOVED` ships as the reference non-trivial scheme.

## Design

### Division of labor & emit scope (what we don't emit, and not clobbering)

A consumer's spec folder holds two different kinds of document; `wt` owns only one:

- **Codebase-derived** (architecture, integration points, style guides) — REMOVED's
  Codebase Analyst produces these from the target repo, or they already live there. `wt` **does
  not emit** them.
- **Product intent + task decomposition** (PRD-ish requirements, the `X.Y.Z` plan) — this is
  what a `wt` spec *is*. `wt` **does** emit this. Mapping: a `wt` **epic** → a Deliverable
  (`X.Y`) with children as tasks (`X.Y.Z`); a **feature** spec → one task (`X.Y.Z`).

Codebase-specific fields a scheme's target wants but `wt` can't know (Primary scope paths, Key
interfaces/contracts, exact build/test commands) are emitted as `<!-- PM/Analyst: fill -->`
markers — a deliberate handoff to the side that *is* in the repo, not a gap we paper over.

Each scheme declares an **emit scope** (which artifacts it owns) so a run can be narrowed:
`--emit project-plan|task-spec|prd`. Export is **additive, idempotent, non-clobbering**:

- Never overwrite an existing file we don't own (architecture/style docs are never touched).
- For a shared file like `project-plan.md`, **splice** our deliverable/tasks in — match on
  `X.Y`/`X.Y.Z` id, update-in-place or skip, preserve everything else (same idempotence as
  SPEC-0014). Re-export without `--force` refuses to clobber divergent content.
- The provenance record (SPEC-0015) captures what `wt` contributed vs. what pre-existed.

### Interface & registry (`src/wt/export_schemes/`)

```python
@dataclass
class OutputFile:
    relpath: str        # path within the target repo, e.g. "specs/tasks/1.2.1-foo.md"
    content: str

class ExportScheme(Protocol):
    name: str                       # "wt-native", "REMOVED"
    description: str
    required_fields: tuple[str, ...]        # canonical spec fields this scheme needs
    def validate(self, spec) -> list[str]   # missing/blocking problems (empty = ok)
    def render(self, spec, cfg) -> list[OutputFile]
```

- `register(scheme)` + `get(name)` + `available()` in a small registry; built-ins registered on
  import. `wt-native` and `REMOVED` ship in-tree.
- **Declarative schemes:** a `TemplateScheme` loads a manifest (`schemes/<name>.toml`: section
  order + label mapping from canonical sections, checkbox enforcement, `id_format`,
  `file_layout`/naming, optional body `template`) and implements `render` by substitution. New
  simple schemes = a manifest file, no code.

### Canonical spec model

The exporter parses an outbound spec (SPEC-0015 frontmatter + `spec_lint.sections`) into a
`CanonicalSpec` (id, title, kind, context, goals, non_goals, decision, design, acceptance[],
test_plan, depends_on[], plus optional target-oriented extras — `scope_paths`,
`verification_commands`, `outcome`, `do`/`dont`, `test_bar` — surfaced from optional
frontmatter/body when present, else left blank for the scheme to mark `<!-- fill -->`).

### `wt-native` scheme

Identity/portable copy — exactly SPEC-0015's current output (portable spec + consumption
contract), refactored to satisfy the interface. Default; `required_fields` = the internal
minimum.

### `REMOVED` scheme (code plugin)

- **Granularity:** a feature spec → one `specs/tasks/<X.Y.Z>-<slug>.md`; an **epic** →
  additionally a `project-plan.md` fragment with a `### Deliverable X.Y` block and a `#### X.Y.Z
  — Title` per child/breakdown item. `X.Y.Z` derived from a configurable base (e.g.
  `outbox_targets[project].task_base = "1.2"`), incrementing the task number.
- **Section mapping:** Context→Context; Goals→Requirements/Functional; Non-goals→Out of Scope;
  Decision+Design→Technical Approach; Acceptance criteria (binary)→Acceptance Criteria; Test
  plan→Verification Steps (each `uv run …`/command line lifted into a fenced Build/Unit/
  Integration/Manual block; prose without commands emitted under Manual with a `<!-- fill -->`);
  `depends_on`→Dependencies.
- **Skeleton markers:** any field REMOVED wants that `wt` lacks (Do/Don't, Test bar,
  scope paths, exact commands) is emitted as the same `<!-- PM: … -->` markers its own preseed
  uses, so its PM completes them.
- **No wt consumption-contract** (REMOVED has its own orchestration); instead emit a short
  `README`/note pointing at the source outbound id for provenance.

### Selection, validation, listing (`src/wt/export.py`, `cli.py`)

- `export_spec(cfg, outbound_id, *, scheme=None, to=None)`: resolve scheme (arg > target cfg >
  `wt-native`); `problems = scheme.validate(canonical)`; if blocking, error listing them (unless
  the scheme is skeleton-tolerant and only *warns*). Write `OutputFile`s via SPEC-0015's atomic
  drop + provenance (now recording the scheme name).
- `wt spec export <id> [--scheme NAME] [--emit ARTIFACT]... [--to PATH] [--force]`; a scheme
  splices into shared files (e.g. `project-plan.md`) and refuses to clobber non-owned or
  divergent content without `--force`. `wt spec schemes` lists name/description/required_fields/
  emittable artifacts.

## Alternatives considered

- **Only ever emit `wt-native` and let each consumer adapt** — rejected; the user explicitly
  wants `wt` to target foreign ingesters, and REMOVED's shape differs enough to need a real
  adapter.
- **Fully declarative schemes only** — insufficient for `REMOVED`'s `SPEC→X.Y.Z`
  decomposition; hence the two-tier (manifest + plugin) design.
- **Fold this into SPEC-0015** — rejected; SPEC-0015 ships the default single-format export, and
  a separate spec cleanly adds the pluggable layer + the first non-trivial adapter without
  rewriting an accepted spec.
- **Complete every downstream field ourselves** — unnecessary and brittle; REMOVED's PM
  refines skeletons, so faithful seeds beat lossy over-specification.

## Acceptance criteria

- [x] An `ExportScheme` registry exists with `wt-native` (default) + `REMOVED`; `wt spec
      schemes` lists them with descriptions + required fields.
- [x] `wt spec export <id> --scheme wt-native` reproduces SPEC-0015's output byte-for-byte
      (no regression), and `--scheme` / `outbox_targets[project].scheme` select the scheme.
- [x] `wt spec export <id> --scheme REMOVED --to <tmp>` writes a `task-spec-template`-shaped
      seed at `specs/tasks/<X.Y.Z>-<slug>.md` (Context/Requirements/Technical Approach/
      Acceptance Criteria/Verification Steps/Dependencies/Out of Scope), with `<!-- PM: … -->`
      markers where `wt` lacks data; an epic also emits a `project-plan.md` deliverable fragment.
- [x] The rendered REMOVED seed parses under its `preseed`/PM expectations (sections present,
      Acceptance Criteria are binary checkboxes, Verification Steps are fenced command blocks).
- [x] A declarative (manifest-only) scheme can be added without new Python and is exercised by a
      test.
- [x] Scheme validation errors on a missing required field before any file is written.
- [x] The `REMOVED` scheme emits **only** its owned artifacts (task-spec / project-plan /
      optional PRD, per `--emit`) and never writes architecture/style/design docs.
- [x] Export is **non-clobbering**: an existing target file we don't own is untouched; a
      pre-existing `project-plan.md` has our deliverable/tasks **spliced in** (other content
      preserved); re-export without `--force` refuses to overwrite divergent content.

## Test plan

- **Automated:** `tests/test_export_schemes.py` — registry lookup + `available()`; `wt-native`
  render equals SPEC-0015's expected bytes; `REMOVED` render of a fixture feature spec yields
  the expected sections/paths/`X.Y.Z`/markers, and of a fixture epic yields the project-plan
  fragment; a manifest-defined `TemplateScheme` renders a simple remap; `validate` blocks a
  spec missing a required field. Golden-file compare for rendered content. CLI (`wt spec export
  --scheme …`, `wt spec schemes`) via `CliRunner` into a tmp target dir.
- **Manual verification:** export a real outbound spec with `--scheme REMOVED --to` a
  throwaway repo laid out like REMOVED; confirm `REMOVED`/its PM would accept the
  seed (sections + markers line up with `task-spec-template.md`).
- **Regression guard:** `uv run pytest` green; SPEC-0015 `wt-native` output unchanged; internal
  `docs/specs` lint untouched.

## Rollout / migration

1. `ExportScheme`/`OutputFile` + registry; refactor SPEC-0015's writer to call `wt-native`.
2. `CanonicalSpec` parse; `TemplateScheme` (manifest tier).
3. `REMOVED` plugin (+ `task_base` config) and `wt spec schemes` / `--scheme`.
4. Tests (incl. golden files) + manual against a REMOVED-shaped repo; close the loop.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 137 passed; `tests/test_export.py` unchanged proves wt-native byte-for-byte + `tests/test_export_schemes.py`); manual verification by the verifier.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- The `X.Y.Z` base for a spec's tasks: per-target config (`task_base`) vs derived from the
  spec/idea vs prompted at export — pin down when wiring the first real target.
- Whether to also emit REMOVED **spec baselines** (free-form context docs) or only the
  per-task seed + project-plan fragment — decide with a real run.

## What shipped / deviations

Implemented as designed: `src/wt/export_schemes/` (`__init__.py` — `OutputFile`/
`RenderContext`/`ExportScheme`/registry; `canonical.py` — `CanonicalSpec`/`parse_canonical`;
`wt_native.py` — SPEC-0015's exact rendering refactored behind the seam; `REMOVED.py` —
the code-plugin adapter; `template_scheme.py` + `manifests/plain-md.toml` — the declarative
tier). `src/wt/export.py` now resolves/validates a scheme and dispatches each rendered
`OutputFile` by its `mode` (`native-spec` / `contract` / `owned` / `splice`) instead of
hard-coding SPEC-0015's two-file write. `src/wt/cli.py`'s `spec export` gained `--scheme`/
`--emit`; added `spec schemes`.

Two deliberate implementation choices not spelled out verbatim in the Design's Python sketch:
- `OutputFile` carries `mode` + `splice_id` (beyond `relpath`/`content`) so `export.py` can
  generically dispatch non-clobber behavior per file without each scheme re-implementing it;
  `ExportScheme.render` takes a `RenderContext` (raw fm/body + the `CanonicalSpec`) rather than
  just the canonical spec, since `wt-native` must reproduce the source body verbatim
  (byte-for-byte), not round-trip it through the canonical model.
- `task_base`/`X.Y.Z` numbering does not scan the target repo for the next free task number
  (no repo access at render time); it always numbers an epic's breakdown children `task_base
  .1`, `.2`, … within a single render. Acceptable per the Open Questions above (still open),
  and safe because the project-plan splice + owned-file non-clobber guard prevent silent
  collisions — a colliding re-run either no-ops (identical) or refuses without `--force`.

Verified: `uv run pytest` — 137 passed (incl. the pre-existing `tests/test_export.py`
unchanged, byte-for-byte, plus the new `tests/test_export_schemes.py`, 19 tests). `python3
tools/spec_lint.py` — exit 0. Manual: rendered a fixture epic (`kind: epic` + a `Breakdown /
sub-specs` list) through `--scheme REMOVED` into a tmp target — produced
`specs/tasks/1.2.1-…md` / `1.2.2-…md` matching `task-spec-template.md`'s section shape
(Context/Requirements[F/NF]/Technical Approach/Acceptance Criteria[checkboxes]/Verification
Steps[fenced Build/Unit/Integration/Manual]/Dependencies/Out of Scope) with `<!-- PM: … -->`
markers for fields wt can't know, plus a `project-plan.md` with `### Deliverable 1.2` /
`#### 1.2.1 — …` / `#### 1.2.2 — …` blocks (REMOVED's bolded fields). Confirmed
`--emit task-spec` skips `project-plan.md`; re-export is idempotent; hand-editing the task
spec or the project-plan's deliverable block and re-exporting without `--force` raises
"different content"; `--force` overwrites.

**Verifier fix:** the initial implementation dropped `project-plan.md` at the target repo
**root**; REMOVED expects it under `specs/` (alongside `specs/tasks/`, per its
`mayor-nudge.md` "specs/project-plan.md" and `REMOVED`). Corrected the `REMOVED`
scheme's relpath to `specs/project-plan.md` and updated the affected tests.
