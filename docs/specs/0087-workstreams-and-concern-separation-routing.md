---
id: SPEC-0087
title: "Workstreams and concern separation (routing, streams, filters, hub; umbrella for priority & sort)"
status: accepted
owner: user
created: 2026-07-28
updated: 2026-07-28
kind: epic
milestone: "M4: cli ergonomics"
source_idea: IDEA-095
tags: [ideas, tasks, workflow, workstream, hub]
---

## Context

Promoted from `IDEA-095` after a cross-cutting explore (org model, CLI/agent surface, related
ledger) and an explicit disposition of every OPEN question.

**Problem.** Speculative idea-lifecycle work and daily actionable work are *mostly* separated
in storage (`org_ideas_file` vs inbox; `is_idea` on `wt tasks` / `wt ideas`), but **triage and
capture** still conflate concerns:

1. **Capture routing** — the `wt idea` vs `wt add` fork is easy to get wrong; SPEC-0044
   explicitly deferred auto-routing actionable/bug-shaped captures to org tasks.
2. **No workstream axis** — `:KIND:` is shape-only (SPEC-0044); `:PROJECT:` is association /
   outbound routing (SPEC-0018/0020/0042), including a live project named `AI-workstreams`.
   There is no orthogonal "lane" shared by ideas and tasks.
3. **Supporting leaks** — `wt agenda` does not filter `is_idea` (scheduled ideas can appear
   beside daily TODOs); `wt ideas` lacks `--project`/`--tag` parity with `wt tasks`; `wt hub`
   is ideas+specs only (no tasks / "today" slice for agents).

Human priority (locked): headline = capture routing + workstream axis; agenda / filter parity /
hub tasks are in-epic supporting children. Mega-epic also umbrellas **IDEA-096** (priorities)
and **IDEA-097** (CLI sorting).

## Goals / Non-goals

**Goals**

- Ergonomic capture routing so actionable work does not silently become speculative ideas
  (including the SPEC-0044 deferred bug→task path as its own child).
- A first-class, **curated** `:WORKSTREAM:` axis on **both** ideas and tasks (single-valued).
- Supporting concern separation: agenda excludes ideas by default (`--ideas` opt-in);
  `wt ideas --project` / `--tag`; hub gains a tasks / today slice.
- Umbrella delivery of priority (096) and sort (097) under this epic's sequencing — not as
  orphan top-level specs.

**Non-goals**

- Overloading `:KIND:` or `:PROJECT:` as workstreams.
- Embeddings / semantic workstream inference.
- Replacing tags (tags remain free-form secondary facets).
- Merging IDEA-106 (OPEN-question promote gate) into this epic — sibling process improvement.
- Changing the single shared `Task` model (SPEC-0012) or inventing a second org datatype.

## Decision

Ship this as a **mega-epic** whose contract is:

1. **Capture routing (child):** make the idea-vs-task fork explicit and, where safe, automatic
   for clearly actionable shapes (esp. bug-kind → `wt add` / inbox keywords), closing
   SPEC-0044's deferred note. Exact policy lives in the child — parent only requires that
   routing is designed, tested, and skill-documented.
2. **`:WORKSTREAM:` (child):** single-valued org property on ideas and tasks; values drawn from
   a **closed enum in config** (not free-form, not tags-only). Filterable on `wt ideas` and
   `wt tasks`. Do **not** reuse the project name `AI-workstreams` as this facet.
3. **Agenda (child):** default `wt agenda` excludes ideas; opt-in `--ideas` if scheduled ideas
   are wanted.
4. **Ideas filter parity (child):** `wt ideas --project` and `--tag` (plumbing already in
   `filter_tasks`).
5. **Hub today (child):** extend `wt hub --json` with an open-tasks / today slice (not a
   separate day-execution command).
6. **Priority (IDEA-096) and sort (IDEA-097):** children under this epic; explore/spec them in
   sequence after the separation spine is accepted, not as independent promotions.

## Architecture / cross-cutting design

- **Axes stay orthogonal:** `state` (lifecycle) × `kind` (shape) × `project` (association /
  routing) × `workstream` (curated lane) × tags (free-form). Children must not collapse these.
- **Config:** e.g. `workstreams: […]` (exact key in the workstream child) validated at capture
  and filter time; unknown values error or warn per child Decision.
- **Property writer:** reuse `org_write.set_property` (already used for lifecycle props).
- **JSON:** additive fields only (`workstream` on idea/task rows when set); hub schema gains a
  tasks array without breaking `wt.hub.v1` consumers beyond documented additive change (child
  may bump/document carefully).
- **Skills / WORKFLOW:** capture and orient document the routing fork and `--workstream`;
  related-search remains orthogonal (SPEC-0086).

## Breakdown / sub-specs

Seedable child ideas (SPEC-0043). Existing **IDEA-096** / **IDEA-097** headings are listed
verbatim so `seed-children` is idempotent once those ideas carry `:EPIC: SPEC-0087`.

- [x] [SPEC-0091](./0091-capture-routing-idea-vs-wt-add-spec-0044-deferred.md) — Capture
      routing: soft warn on `--kind bug` + skills/WORKFLOW; `--force-idea` escape.
- [x] [SPEC-0090](./0090-curated-workstream-on-ideas-and-tasks.md) — Curated :WORKSTREAM: on
      ideas and tasks (config enum, capture + filters + idea mutator).
- [x] [SPEC-0088](./0088-default-wt-agenda-excludes-ideas-ideas-opt-in.md) — Agenda excludes
      ideas by default (--ideas opt-in).
- [x] [SPEC-0089](./0089-wt-ideas-project-and-tag-filter-parity.md) — wt ideas --project and
      --tag filter parity.
- [x] [SPEC-0092](./0092-hub-tasks-today-slice.md) — Hub tasks / today slice (+ `wt tasks --json`).
- [x] [SPEC-0093](./0093-priority-surfacing-parity-for-ideas-filter-column.md) — Priority
      surfacing parity for ideas (filter, column, JSON, mutate).
- [x] [SPEC-0094](./0094-optional-sort-on-wt-ideas-and-wt-tasks-not-global.md) — Optional
      --sort on wt ideas and wt tasks (freshness|priority; --desc).
- [x] [SPEC-0096](./0096-filter-parity-for-wt-next-hub-and-agenda.md) — Filter parity for
      wt next, hub, and agenda.

Sequencing / dependencies:

1. Agenda exclusion and ideas `--project`/`--tag` can land in parallel early (small, unblocks
   triage).
2. `:WORKSTREAM:` next (depends on clear axis contract above; may land filters in the same
   child).
3. Capture routing after or parallel to workstream (skills must mention both).
4. Hub tasks slice after tasks JSON shape is stable enough (may introduce `wt tasks --json` if
   needed as a dependency inside that child).
5. Priority (096) then sort (097) — presentation/metadata after separation spine exists so
   filters compose (`--workstream` × `--priority`, `--sort`).

## Acceptance criteria

- [ ] An actionable capture has a designed, documented path that does not rely on hoping the
      human picks `wt add` (child AC define the exact automation vs guidance bar).
- [ ] Ideas and tasks can carry a curated `:WORKSTREAM:` and be filtered by it on both list
      commands.
- [ ] Default `wt agenda` never lists idea headlines; `--ideas` can include them.
- [ ] `wt ideas` supports `--project` and `--tag`.
- [ ] `wt hub --json` includes a tasks/today slice usable by agents.
- [ ] IDEA-096 and IDEA-097 are explored/specced/done (or superseded) as children of this epic,
      not as independent top-level promotions.
- [ ] `:KIND:` and `:PROJECT:` semantics unchanged; project `AI-workstreams` is not overloaded
      as the workstream facet.

## Test plan

Integration-level (children own unit tests):

- **Integration/e2e:** after children land, a fixture with mixed ideas+tasks across two
  configured workstreams proves: filter by workstream on both commands; agenda default hides
  a scheduled idea; hub JSON contains both open ideas and open tasks; capture-routing child
  scenarios pass as specified there.
- **Manual verification:** morning ritual (`wt ideas`, `wt agenda`, `wt hub --json`) on a real
  corpus with at least one workstream set; confirm project `AI-workstreams` still routes as a
  project, not a workstream value unless explicitly configured as such in the enum (should
  not be required).
- **Regression:** `uv run pytest`; idea/task separation (`is_idea`) and SPEC-0044 kind glyphs
  unchanged.

## Rollout / sequencing

Land supporting filter/agenda fixes first for immediate triage relief; then `:WORKSTREAM:` +
capture routing; then hub slice; then 096/097. Partial delivery is useful: each child should
leave the CLI coherent on its own.

## Definition of done

- [ ] All child specs `done` or `superseded` (the linter gates this).
- [ ] Integration test plan executed; `uv run pytest` green.
- [ ] Acceptance criteria met; epic body reflects what shipped.
- [ ] `docs/LEDGER.md` regenerated.

## Open questions

(none — IDEA-095 dispositions 2A–10B locked 2026-07-28; child specs may open narrower questions)
