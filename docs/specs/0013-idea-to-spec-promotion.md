---
id: SPEC-0013
title: Idea → spec promotion
status: done
owner: user
created: 2026-07-16
updated: 2026-07-17
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [ideas, specs, org]
parent: SPEC-0011
depends_on: [SPEC-0012]
---

## Context

The connective tissue of the [SPEC-0011](./0011-idea-to-spec-pipeline.md) epic: turn a ripe
idea ([SPEC-0012](./0012-idea-capture-and-model.md)) into a **scaffolded internal spec**,
prefilled from its org subtree, with a durable bidirectional link — removing boilerplate, not
the thinking.

## Goals / Non-goals

**Goals**
- `wt spec new --from-idea <sel>` scaffolds a `docs/specs/NNNN-slug.md` from the template,
  prefills **Context** from the idea's org subtree (heading + incubation notes), and picks the
  next free spec number + a slug.
- Bidirectional link: the org idea gets a `:SPEC:` property; the spec gets a `source_idea:`
  frontmatter field. The idea advances `IDEA/INCUBATE → SPECCED`.
- `--epic` scaffolds from `TEMPLATE-epic.md`.

**Non-goals**
- Filling in Decision/Design/etc. (human authxxs those; the spec starts `draft`).
- Task generation (SPEC-0014) or outbound specs (SPEC-0015).
- Auto-`accepted` — a scaffolded spec is `draft` until a human promotes it.

## Decision

Add `wt spec new --from-idea <sel> [--epic] [--title T]`. It reads the idea via
`resolve_selector`, computes the next id from `docs/specs/`, copies the appropriate template,
substitutes frontmatter (`id`, `title`, `created`, `source_idea`) and the prefilled Context,
writes the file, then `set_state`s the idea to `SPECCED` and writes the `:SPEC:` property back
into the org file. `source_idea` is added to `spec.schema.json` (optional string).

## Design

### Schema (`docs/specs/spec.schema.json`, `SCHEMA.md`)

Add optional `source_idea` (string: the idea's `id` — `:ID:` or `file:line`). `additionalProperties`
stays false, so it must be declared. Document it in `SCHEMA.md`.

### Promotion (`src/wt/specs.py`, new)

- `next_spec_number()` — max existing `docs/specs/NNNN-*.md` + 1, zero-padded.
- `slugify(title)` — kebab-case.
- `scaffold_from_idea(cfg, selector, *, epic=False, title=None) -> (spec_path, spec_id)`:
  1. `task = resolve_selector(cfg, selector)` (must be an idea; else error).
  2. `title = title or task.heading`.
  3. Read the idea's **subtree** text (heading + body/notes) from the org file (reuse the
     subtree-range logic) → the prefilled **Context**.
  4. Copy `TEMPLATE-epic.md` if `--epic` else `TEMPLATE.md`; fill `id`, `title`, `created`
     (today via `cfg["_tz"]`), add `source_idea: <task.id>`, and inject the Context prose.
  5. Write `docs/specs/NNNN-slug.md`.
  6. `org_write.set_state(cfg, task, "SPECCED")`; add/update the idea's `:SPEC:` property to the
     new spec id (a small property-writer, sibling to `set_state`, reusing backup+atomic write).
- Idempotence guard: if the idea already has a `:SPEC:` property, error (already promoted) unless
  `--force`.

### CLI (`src/wt/cli.py`)

```
wt spec new --from-idea "instant review agent"          # -> docs/specs/00NN-instant-review-agent.md (draft)
wt spec new --from-idea idea-42 --epic --title "Review platform"
```

Prints the created path + the reciprocal link. (`wt spec …` is a new command group; it does
**not** wrap `tools/spec_lint.py`, which stays a dev tool per SPEC-0002.)

## Alternatives considered

- **Link only one way (spec→idea)** — rejected; the org side needs `:SPEC:` so `wt ideas` can
  show promotion status and humans see it in Emacs.
- **Generate an `accepted` spec** — rejected; scaffolding ≠ deciding. Starts `draft`.
- **LLM-fill the whole spec** — out of scope; deterministic scaffold keeps it reviewable and
  offline.

## Acceptance criteria

- [x] `wt spec new --from-idea <sel>` creates a lint-valid `draft` spec at the next free number,
      with Context prefilled from the idea's subtree and `source_idea` set.
- [x] The org idea gains a `:SPEC:` property pointing at the new spec id and moves to `SPECCED`.
- [x] `--epic` uses the epic template; `--title` overrides the derived title.
- [x] Re-promoting an already-linked idea errors unless `--force`.
- [x] `python3 tools/spec_lint.py` passes on the scaffolded spec (schema knows `source_idea`).

## Test plan

- **Automated:** `tests/test_promote.py` (tmp specs dir + tmp org): scaffold from a fixture
  idea; assert the new file exists, frontmatter (`id`/`source_idea`) is correct, Context
  contains the idea's notes, the spec passes `spec_lint.validate`, the org idea has `:SPEC:` +
  state `SPECCED`, and re-promote errors without `--force`. CLI via `CliRunner`.
- **Manual verification:** promote an idea from a copy of `ai/ideas.org`; open both files.
- **Regression guard:** existing specs still lint; `uv run pytest` green.

## Rollout / migration

1. `source_idea` in schema + SCHEMA.md. 2. `src/wt/specs.py` (numbering, slug, scaffold) +
property-writer. 3. `wt spec new` CLI. 4. Tests + manual; close the loop.

## What shipped

Implemented as designed, no deviations. `spec.schema.json`/`SCHEMA.md` gained optional
`source_idea` (string). `src/wt/org_write.py` gained `set_property(cfg, task, name, value)`,
sibling to `set_state`: line-anchored + drift-guarded on the headline, finds/creates the
`:PROPERTIES:` drawer immediately after the headline (and any SCHEDULED/DEADLINE/CLOSED
lines), backs up + writes atomically. New `src/wt/specs.py`: `next_spec_number(specs_dir)`,
`slugify(title)`, `scaffold_from_idea(cfg, selector, *, epic=False, title=None, force=False)`.
The specs directory is injectable via `cfg["specs_dir"]` (default
`Path.cwd() / "docs/specs"`); templates are read from the same directory, which is how tests
avoid touching the real `docs/specs/`. Promotion order is: write the `:SPEC:` property first,
then `set_state(..., "SPECCED")` — reversing the Decision's stated order — because writing the
property after the state flip would trip `set_state`'s own drift guard on a stale `task.state`;
writing the property first leaves the headline's state token untouched until `set_state` runs.
Idempotence: `task.properties.get("SPEC")` (already parsed by `orgparse`/`Task`) gates
re-promotion unless `--force`. CLI: `wt spec new --from-idea <sel> [--epic] [--title T]
[--force]`, added as a new `@cli.group("spec")` with a `new` subcommand (per the brief, ready
for future `spec` subcommands from later specs).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 91 passed; `tests/test_promote.py`);
      manual verification performed by the verifier (temp-dir scaffold: draft + `source_idea` +
      Context prefill, `:SPEC:`/`SPECCED` on the idea, idempotence raise).
- [x] No regressions.
- [x] Spec body updated to match what shipped (incl. the property-before-state-flip deviation).
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._

**Follow-up (post-done):** `slugify` had no length cap, so promoting an idea whose heading is a
whole paragraph produced a filename over the OS limit (`OSError: File name too long`). Capped
`slugify` to 50 chars (word-boundary) and added `_short_title` (truncates a long heading to a
~70-char spec title; full text still lands in Context). Regression tests added.
