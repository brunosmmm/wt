---
id: SPEC-0142
title: "Docs product IA, narrative, and glossary"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0141
tags: [docs]
depends_on: [SPEC-0141]
source_idea: IDEA-355
---

## Context

Child of [SPEC-0141](./0141-human-product-documentation-site-showcase.md). Before a
themed site can ship, the **nav map**, **home narrative**, and **glossary** must exist
as curated Markdown under `docs/product/`.

## Goals / Non-goals

**Goals**

- Create `docs/product/` with home, concepts/glossary, guide stubs, capability stubs,
  reference stub, contribute page.
- Lock dual-capability wording on the home page.
- Nav structure matches SPEC-0141 Architecture (ready for MkDocs nav).

**Non-goals**

- MkDocs/`mkdocs.yml` (SPEC for IDEA-356).
- Full guide or capability prose depth (later children).
- Rewriting `docs/specs/` or deleting WORKFLOW.md yet (README slim is IDEA-360).

## Decision

Land the IA as real files under `docs/product/` now. Stubs include a one-paragraph
purpose + “Status: stub — filled by SPEC-0141 child …” so the tree is honest and
buildable.

## Design

```
docs/product/
  index.md
  concepts/index.md          # glossary
  guides/
    index.md
    getting-started.md
    track-time.md
    idea-to-ship.md
    outbound.md
    multi-project.md
  capabilities/
    index.md
    report.md ideas.md tui.md hub.md projects.md
    sheet.md clock.md completion.md release-archive.md
    tasks-agenda.md meetings.md skills.md
  reference/index.md
  contribute/index.md
```

Home narrative (required phrases): passive time tracking; idea→ship pipeline;
`clock-in` supplemental.

## Acceptance criteria

- [x] `docs/product/` tree exists with home, glossary, guides index + 5 guide stubs,
      capabilities index + major surface stubs, reference stub, contribute page.
- [x] Home states both capabilities and clarifies clock-in vs passive tracking.
- [x] Glossary defines ≥12 core terms used across guides.
- [x] No MkDocs config required for this spec to be `done` (files only).

## Test plan

- **Automated:** path existence check in a small pytest or assert via script in CI later;
  for this slice: `test_docs_product_ia_tree.py` checks required paths + home keywords.
- **Manual:** open `docs/product/index.md` — narrative reads as one product.

## Definition of done

- [x] AC met; tests pass; ledger updated; idea reconciled.

## Open questions

None.
