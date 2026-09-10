---
id: SPEC-0011
title: Idea → spec → export pipeline
status: done
owner: user
created: 2026-07-16
updated: 2026-07-18
milestone: "M3: idea→spec pipeline"
kind: epic
tags: [ideas, specs, org, export]
depends_on: [SPEC-0005, SPEC-0010]
---

## Context

`wt` now spans a work-lifecycle spine — org **tasks**, tracked **time**, and its own
**spec** discipline — all joined by one topic/JIRA/repo key. The left end of the funnel is
missing: **ideas** (things that are not yet actionable tasks, but seeds that need
incubation) and the connective tissue that turns a ripe idea into a **spec**, and a spec
into **tasks** (whose tracked time then joins back). The user also wants the strategic
extension: generate specs that agents in **other repos** can consume to implement, so `wt`
becomes a spec *factory*, not just an internal spec *consumer*.

Substrate already exists: `~/work/org/ai/ideas.org` holds freeform idea headlines that accrue
incubation notes (checkboxes, prose) but have no lifecycle state today.

The full spine this epic completes:

```
idea → spec → task/epic → tracked time → digest
(org)  (spec)   (org)       (transcripts)  (join)
```

## Goals / Non-goals

**Goals**
- First-class **ideas** in org with a lifecycle (capture, incubate, promote/drop), kept out of
  actionable task views.
- **Promotion**: scaffold a spec from an idea (prefilled from its org subtree), with a
  bidirectional link, advancing the idea's state.
- **Generation**: emit org tasks/epics from an accepted spec's breakdown, keyed so their time
  joins in `wt digest`.
- **Outbound export**: portable specs targeted at an external repo, exported by file-drop into
  that repo with a consumption contract, provenance kept in `wt`.

**Non-goals**
- Auto-*writing* spec content (LLM authxxing). We scaffold + prefill; the human finishes it.
- A live sync/status protocol with other repos (file-drop only; see SPEC-0015).
- Replacing the internal governance spec system — outbound specs are a **parallel** namespace.
- Idea → task without a spec in between (the pipeline's discipline is intentional).

## Decision

Model this as two layers, built in order:

- **Layer 1 — internal funnel** (idea → spec → task): SPEC-0012 (idea capture & model),
  SPEC-0013 (idea→spec promotion), SPEC-0014 (spec→task generation). Uses the existing
  `docs/specs/` governance system unchanged.
- **Layer 2 — outbound factory** (SPEC-0015): outbound specs carry a `target_project`/
  `target_repo`, live in a **separate store** (`docs/outbox/`) with their own index + id
  namespace, and export by **file-drop** into the target repo. Depends on Layer 1's
  scaffolding.

Locked decisions (with the user): **parallel namespace** for outbound specs, ideas modeled as
an **org keyword set**, consumption by **file-drop into the target repo**.

## Architecture / cross-cutting design

**Ideas (org).** New config `org_ideas_file` (default `~/work/org/ai/ideas.org`) and
`org_idea_keywords` (default `["IDEA", "INCUBATE", "SPECCED", "|", "PROMOTED", "DROPPED"]`).
The ideas file declares that keyword set via `#+TODO`. `Task` gains a derived **`is_idea`**
(its `state` is in the idea vocabulary), so ideas reuse the whole SPEC-0005 parser / SPEC-0010
`add_task` / SPEC-0009 write-back pipeline, yet — being non-actionable — stay out of the
default `wt tasks` view. `wt idea "…"` captures; `wt ideas` lists.

**Promotion (idea → spec).** `wt spec new --from-idea <sel>` copies `TEMPLATE.md` /
`TEMPLATE-epic.md`, prefills **Context** from the idea's org subtree (heading + notes), writes
a **bidirectional link** — the org idea gets a `:SPEC:` property, the spec gets a
`source_idea:` reference — and advances the idea `IDEA → SPECCED` via `set_state`.

**Generation (spec → task).** From an accepted spec's *Breakdown*, `wt` emits org tasks via
`add_task`, carrying the spec/JIRA key so their tracked time joins in `wt digest`; the source
idea advances `SPECCED → PROMOTED`.

**Outbound (Layer 2).** Outbound specs are a **parallel namespace**: stored under
`docs/outbox/<project>/`, ids namespaced per project (e.g. `<PROJ>-NNNN`), indexed by their own
light index (not `docs/LEDGER.md`), reusing the internal *schema/template shape* plus
`target_project`/`target_repo`. `wt spec export <id> --to <repo-path>` drops a portable spec +
a short `AGENTS.md`-style consumption contract into the target repo; `wt` retains the canonical
copy + provenance. The internal `tools/spec_lint.py` (which scans `docs/specs/[0-9]*.md`) is
**untouched** — outbound specs get their own validation so they never pollute `wt`'s ledger.

**Pluggable output schemes (Layer 2, SPEC-0016).** Different consumers ingest different spec
shapes, so the exporter delegates to a selectable **scheme/adapter**: `wt-native` (default) is
our own shape; `wt-native` renders an outbound spec into the the target consumer `task-spec-template`/
`project-plan` shape (`X.Y.Z` task ids, `<!-- fill -->` skeleton markers its PM refines).
Schemes are two-tier — declarative manifests for simple relabels, code plugins for real
decomposition — selected via `--scheme` or per-target config.

**Driving the pipeline (SPEC-0017).** The whole funnel is operated through the `wt` **CLI**
(the stable interface — internals are never read) plus a few thin, installable **skills** (the
playbooks encoding the multi-step workflow + conventions), so a fresh agent session can start
new work without re-understanding the codebase.

**Reuse:** `org.load_tasks`/`filter_tasks`, `org_write.add_task`/`set_state`, the spec
`TEMPLATE*.md` + schema, `report`/`console` rendering, `topics.KEY_RE` for the join key.

## Breakdown / sub-specs

- [x] SPEC-0012 — Idea capture & model (config, `Task.is_idea`, `wt idea`, `wt ideas`). *(depends_on 0005, 0010)* — Layer 1
- [x] SPEC-0013 — Idea → internal spec promotion (`wt spec new --from-idea`, prefill, bidi link). *(depends_on 0012)* — Layer 1
- [x] SPEC-0014 — Spec → org task/epic generation (breakdown → tasks, keyed for the join). *(depends_on 0012, 0013)* — Layer 1
- [x] SPEC-0015 — Outbound portable specs + cross-project export (parallel namespace, file-drop). *(depends_on 0013)* — Layer 2
- [x] SPEC-0016 — Pluggable export schemes + downstream adapter (`wt-native` default + `wt-native`). *(depends_on 0015)* — Layer 2
- [x] SPEC-0017 — Agent workflow skills (drive the pipeline from a fresh session without reading code). *(depends_on 0012–0016)* — usability

Sequencing: 0012 → 0013 → {0014, 0015} → 0016, then 0017 (skills over the whole surface). Layer 1 = 0012+0013+0014 is independently useful; Layer 2 = 0015 (file-drop export) then 0016 (multi-scheme adapters) is the strategic payoff; 0017 makes it all drivable without reading `wt`'s code.

## Acceptance criteria

- [x] An idea can be captured, listed, incubated, and promoted to a spec with a working
      bidirectional link; its state advances IDEA → SPECCED → PROMOTED.
- [x] A promoted spec can generate org tasks whose tracked time joins in `wt digest`.
- [x] An outbound spec can be authxxed in the parallel namespace and **exported by file-drop**
      into a (temp) target repo with a consumption contract, without touching `docs/LEDGER.md`
      or `tools/spec_lint.py`'s internal scan.
- [x] Export is **scheme-selectable**: `wt-native` (default) plus a `wt-native` adapter that
      renders an outbound spec into the target consumer's ingestible shape.
- [x] The pipeline is **drivable from a fresh session** via installable skills over the CLI,
      without reading `wt`'s source.
- [x] All child specs are `done`/`superseded`.

## Test plan

- **Integration/e2e:** a fixture funnel — capture an idea, `spec new --from-idea` scaffolds a
  lint-clean spec with the bidi link, `spec generate` emits keyed org tasks (assert one joins a
  synthetic tracked topic), and (0015) `spec export` drops files into a temp target dir. Assert
  the internal ledger + `spec_lint` are unaffected by outbound artifacts.
- **Manual verification:** run the funnel against a copy of real `ai/ideas.org`.
- **Spec system:** `python3 tools/spec_lint.py` stays green; epic done-gating enforces all
  children finished before SPEC-0011 → done; `tests/test_specs.py` in the pytest run.

## Rollout / sequencing

Land 0012 → 0013 → 0014 (Layer 1) → 0015 (Layer 2), each closing its own loop. Partial
delivery is useful: after 0012+0013 you can capture and promote ideas; 0014 closes the
internal funnel; 0015 turns it into a cross-project spec factory.

## Definition of done

- [x] All child specs `done` or `superseded` (the linter gates this).
- [x] Integration test plan executed; `uv run pytest` green.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

- Outbound id scheme (`<PROJ>-NNNN` vs a UUID vs mirroring the target repo's own numbering) —
  to be pinned down in SPEC-0015.
