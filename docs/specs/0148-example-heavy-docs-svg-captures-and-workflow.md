---
id: SPEC-0148
title: "Example-heavy docs: SVG captures and workflow architecture"
status: accepted
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: epic
tags: [docs]
depends_on: [SPEC-0141]
source_idea: IDEA-382
---

## Context

SPEC-0141 shipped a navigable product site, but pages are still mostly command inventories.
Newcomers cannot *see* the CLI/TUI or the workflow architecture. This epic adds **real SVG
captures** and **workflow block diagrams** to the product docs.

Promoted from `IDEA-382`.

## Goals / Non-goals

**Goals**

- Deterministic demo fixture (no live org data) for docs captures.
- Real SVG from Rich (CLI) and Textual (`IdeaDesk.export_screenshot`).
- Regenerable capture script checked into the repo.
- Workflow/architecture diagrams on guides (idea→ship, time pipeline, outbound).
- Guides rewritten to be example- and workflow-centric, embedding captures + diagrams.

**Non-goals**

- PNG/asciinema as the primary artifact.
- Capturing a contributor's live XDG corpus into git.
- Baking a permanent diagram DSL before content exists (Mermaid default; D2 later OK).

## Decision

Ship a **capture pipeline + content** epic. SVG from Rich/Textual on a seeded fixture.
Diagrams default to **Mermaid** in MkDocs Material (fast path); treat D2 (or similar) as a
drop-in that can pre-render to SVG later without changing guide structure.

## Architecture / cross-cutting design

```
scripts/docs-capture.py
  → builds tmp demo cfg + org ideas (+ optional tiny history)
  → patches wt.console / wt.report console to Console(record=True, width=…)
  → calls report.ideas / next_ideas / report
  → save_svg → docs/product/assets/captures/*.svg
  → headless IdeaDesk.run_test → export_screenshot → *.svg

docs/product/guides/*.md  embed ![](../assets/captures/…) + mermaid fences
docs/product/concepts/workflows.md  (or sections in guides) hold architecture diagrams
```

**Invariants**

- Captures must be regenerable with `uv run python scripts/docs-capture.py`.
- Fixture data is fictional and stable (fixed titles/ids).
- MkDocs `--strict` stays green (assets linked must exist).

## Breakdown / sub-specs

- [x] Org-mode storage guide + expanded CLI SVG captures — SPEC-0152

- [x] Demo fixture + docs SVG capture toolchain (project: Meta-Tools) — SPEC-0149
- [x] Workflow architecture diagrams (project: Meta-Tools) — SPEC-0150
- [x] Example-heavy guide rewrites embedding captures + diagrams (project: Meta-Tools) — SPEC-0151
- [ ] Capability pages embed representative shots where helpful (project: Meta-Tools)

Sequencing: 1 → 2 and 3 (3 needs at least one capture set); 4 after 1.

## Acceptance criteria

- [ ] Product guides show real CLI and TUI SVG captures from the capture script.
- [ ] Idea→ship, time-tracking, and outbound flows have architecture/workflow diagrams.
- [ ] Captures regenerate without live user data.
- [ ] `mkdocs build --strict` and docs tests stay green.

## Test plan

- **Integration:** capture script exits 0; SVG files non-empty; mkdocs strict; pytest asserts
  required capture paths exist.
- **Manual:** open getting-started / idea→ship / desk capability; confirm SVGs render.
- **Regression:** existing docs tests + suite green.

## Rollout / sequencing

Land toolchain first so later children are Markdown + regen. Keep SPEC-0141 site as host.

## Definition of done

- [ ] All child specs `done` or `superseded`.
- [ ] Integration test plan executed; site builds strict.
- [ ] Acceptance criteria met; epic body reflects what shipped.
- [ ] `docs/LEDGER.md` regenerated.

## Open questions

- Diagram DSL beyond Mermaid (D2 etc.) — deferred to diagram child; Mermaid is the default
  until a child decides otherwise.
