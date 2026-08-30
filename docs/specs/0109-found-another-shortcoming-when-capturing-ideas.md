---
id: SPEC-0109
title: "Idea project association: set_idea_project library gap and desk wiring"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
depends_on: [SPEC-0102, SPEC-0103]
milestone: "M5: interactive desk"
source_idea: IDEA-139
tags: [tui, org, capture, bug]
---

## Context

From `IDEA-139`, reported from real use: an idea captured in the desk can never be given a
`:PROJECT:` — not at capture, not afterwards.

**The gap is library-wide, not TUI-specific** (verified 2026-07-30):

- `org_write` has `set_idea_kind`, `set_idea_workstream`, `set_idea_priority`, `set_idea_tags`
  — and **no project equivalent**.
- `wt idea` has no `project` subcommand. `--project` exists **only** on capture.
- So even a classic-CLI user cannot give a project to an idea captured without one.

The desk merely made an existing hole obvious. This is the same shape as
[SPEC-0101](./0101-library-gaps-for-question-crud-and-idea-tags.md), where question CRUD had to
land in the library before the desk could offer it.

**Why it matters.** `:PROJECT:` drives `--project` filtering across `wt ideas` / `wt next` /
`wt hub` (SPEC-0089/0096) and keys SPEC-0042 research-context resolution. A project-less idea
reports `research: (none) — no :PROJECT:` and is invisible to project-scoped triage — so
desk-captured ideas are second-class the moment they are written. IDEA-137/138/139 all show
exactly that line, this bug demonstrating itself.

## Goals / Non-goals

**Goals**
- `set_idea_project(cfg, selector, project)` in `org_write`, with the permissive contract.
- `wt idea project <SELECTOR> --set <NAME>` in the classic CLI, so the gap closes for everyone.
- Desk: choose a project **at capture**, and change it afterwards from the `m` metadata chooser.
- Clearing a project is possible (mis-set is as likely as unset).

**Non-goals**
- A project registry, or making projects a closed vocabulary — `known_projects` stays derived
  from `mappings.yaml` (SPEC-0018).
- Changing `--project` filtering, research-context resolution, or `outbox_targets`.
- Retro-assigning projects to existing project-less ideas (a separate, data-shaped job).
- Epic/key association (`--epic`, `--key`) — same family, not this spec.

## Decision

Land the library mutator plus a thin CLI verb **first**, then wire the desk to it — the
SPEC-0101 sequencing. The desk gains a project step in the capture flow and a `project` entry in
the metadata chooser, both calling `apply_mutation`, so the one-mutator-path invariant holds.

## Design

**Library.** `set_idea_project(cfg, selector, project)` writing `:PROJECT:` via the existing
`set_property`, mirroring `set_idea_workstream`'s shape (resolve selector → reject non-ideas →
write → stamp `:UPDATED:`).

- **Permissive, per SPEC-0018.** An unknown project **warns and still writes**
  (`_warn_unknown_associations`). This spec must not quietly turn a deliberately permissive
  association into validation.
- `project=None` / `""` clears the property, matching `set_question_priority(None)`.

**CLI.** `wt idea project <SELECTOR> --set <NAME>` (`--set ""` clears), shell-completing from
`known_projects` the way `--project` already does.

**Desk.**
- *Capture:* after the text prompt, offer a project chooser built from `known_projects(cfg)`,
  with an explicit **"(none)"** entry so capture stays one extra keypress and never forces a
  choice. `capture_idea` grows an optional `project` argument passed to `add_idea(project=…)`,
  so a captured idea is written with its project rather than written then patched.
- *After capture:* `project` joins kind / priority / workstream in the `m` chooser
  (SPEC-0103), which is already a two-step field→value flow and needs no new chrome.
- `apply_mutation` gains a `project` action. No new write path.

**Default (idea Q4).** When the desk was opened with `--project P`, that is the pre-selected
entry in the chooser — the filter you are working under is the project you are almost certainly
capturing into. Pre-selected, never silently applied.

## Alternatives considered

- **Desk-only fix, patching `:PROJECT:` through `set_property` directly** — rejected: invents a
  write rule in the UI, which SPEC-0098's one-mutator-path invariant forbids, and leaves CLI
  users with no way to set a project at all.
- **Free-text project entry only** — rejected as the *primary* affordance: `known_projects`
  already exists and typing a project name by hand is how they drift. Free text remains
  reachable, since the contract is permissive.
- **A closed chooser that rejects unknown projects** — rejected: it would silently reverse
  SPEC-0018's deliberate "warn, never block".
- **Prompting for project on every capture, mandatory** — rejected: capture must stay fast; an
  idea with no project is a valid state today and should remain one.

## Acceptance criteria

- [x] `set_idea_project` sets and clears `:PROJECT:`, warns (never blocks) on unknown, rejects
      non-ideas, and stamps `:UPDATED:`.
- [x] `wt idea project ID --set NAME` works, and `--set ""` clears.
- [x] Desk capture can attach a project, including choosing none.
- [x] Desk `m` chooser can set and clear a project on an existing idea.
- [x] A desk-captured idea with a project is visible to `wt ideas --project` and resolves
      research context.
- [x] No new write path: the desk goes through `apply_mutation`.

## Test plan

**Executed 2026-07-30.** `tests/test_idea_project.py` — 19 tests (15 need no Textual).

- **Library:** set / change / clear; unknown project **warns on stderr and still writes**;
  non-idea rejected; `:UPDATED:` stamped; sibling properties and the headline survive a
  set-then-clear round trip.
- **Clearing removes the line**, it does not blank it — asserted on the file body
  (`":PROJECT:" not in body`), because `ideas.org` is hand-edited.
- **CLI:** `--set` / `--set ""` round trip; `--set` required; a bad selector is a clean error
  with no traceback.
- **Consequences** (why the missing field mattered): an idea is *invisible* to
  `wt ideas --project Example --json` before, and found after; `wt idea show --json` research
  context changes from the `no :PROJECT:` form once a project is set.
- **Desk:** `capture_idea` is asserted to pass `project=` **into `add_idea`** via a spy, so the
  idea is written associated rather than patched afterwards; capture without a project works for
  `None`/`""`/whitespace; `apply_mutation` sets and clears; the chooser list comes from the
  registry and **degrades to empty** rather than raising when no mappings are configured; a
  guard that `app.py` names neither `set_property` nor `set_idea_project` directly.
- **Pilot:** capture → project chooser → set; capture → decline (pre-selected `(none)`); the `m`
  chooser sets *and* clears; a desk opened with `--project Example` pre-selects it.
- **Manual verification** in an isolated `WT_CONFIG_DIR`: `wt idea project --set Example` flipped
  research context off the `no :PROJECT:` line and `wt ideas --project Example` found it;
  `--set Nonesuch` printed `! unknown project 'Nonesuch'; known projects: Meta-Tools, Example`
  **and wrote it**; `--set ""` left **zero** `PROJECT` lines in the file. Driving the desk wrote
  `:PROJECT: Meta-Tools` into the new idea's drawer at creation.
- **Regression guard:** `uv run pytest` — full suite green; desk suites (74 TUI tests) pass.

Two tests were rewritten after first passing, because they could not fail: one asserted
`backups is not None` (meaningless) and now spies on `add_idea`'s kwargs; the other ended
"cleared or unchanged is acceptable" and now walks the chooser back to `(none)` and asserts the
clear.

## Rollout / sequencing

1. `set_idea_project` + CLI verb (useful alone — closes the gap for classic users).
2. Desk metadata chooser entry.
3. Capture-time project.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — all four resolved on IDEA-139: capture-time *and* post-hoc; chooser from
`known_projects` with free text still permitted; CLI verb included; desk `--project` pre-selects)
