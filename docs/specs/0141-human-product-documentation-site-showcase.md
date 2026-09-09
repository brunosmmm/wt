---
id: SPEC-0141
title: "Human product documentation site: showcase + workflow guides"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: epic
tags: [docs, workflow, site]
depends_on: []
source_idea: IDEA-354
---

## Context

`wt` ships two complementary capabilities: **passive time tracking** (transcripts →
hours) and an **idea → explore → spec → generate/export → verify** pipeline (desk, hub,
outbound, skills). Substance already exists — root README, `docs/WORKFLOW.md`,
`docs/specs/` + ledger, agent skills — but humans discover it by stitching three genres
together. There is no themed, navigable product site that showcases capability and teaches
workflow end-to-end.

This epic delivers that system. Child specs implement slices; this epic locks IA,
tooling choice, and what “done” means for the assembled site.

## Goals / Non-goals

**Goals**

- A **capability showcase** that makes the full CLI/product surface discoverable
  (tracking, ideas, TUI, hub, projects/outbound, sheet, clock, completion, …).
- **Workflow-centric guides** for humans: day-1, daily ritual, time-tracking loop,
  idea→ship (internal + outbound), multi-project.
- **Modern themed rendering** (nav, search, mobile-friendly) from Markdown in-repo.
- Clear **audience split**: product site for humans; skills remain the agent OS; specs
  remain the engineering decision record (linked, not replaced).
- Root README becomes a **short front door** into the site, not a competing essay.

**Non-goals**

- Replacing or rewriting the spec ledger as the primary human path.
- Translating every SPEC-NNNN into a tutorial.
- Replacing agent skills with the product site.
- Perfect historical accuracy of every past README paragraph before the site ships
  (drift fixes land in the reference/README child).

## Decision

Build a **curated product docs tree** (guides + concepts + how-to + reference +
capability pages) rendered with **MkDocs Material** (Python-native, excellent theming,
search, versioning-friendly). Keep `docs/specs/` as the decision archive; surface it as
an optional “Decisions / ledger” section or deep links from product pages — not the home
path.

**Product narrative (mandatory on the home page):** wt is both (1) passive engagement
hours from transcripts/meetings and (2) a governed idea→ship workflow. Org `clock-in` is
**supplemental wall-time** for intentional slices — it does not replace passive tracking.

## Architecture / cross-cutting design

```
docs-site/   (or docs/product/ — child chooses path)
  index.md              home: dual capability + CTAs
  concepts/             glossary (topic, facet, idea, task, hub, desk, outbound, …)
  guides/               getting-started, track-time, idea-to-ship, outbound, multi-project
  capabilities/         one page per major surface (report, tui, hub, projects, …)
  reference/            command reference (curated or generated from --help)
  contribute/           pointer to AGENTS.md + specs SCHEMA (how we change wt)
mkdocs.yml              Material theme, nav, search
```

**Invariants**

- Live CLI is source of truth for flags; reference pages must not invent flags.
- Workflow guides prefer `wt <cmd>` + skills stage names; link SPECs only for “why”.
- Agent readers get one page: “Using wt with agents” → install skills + `/wt-orient`.
- CI (or local `make docs`) builds the site; broken nav fails the build.

**Sequencing:** IA + narrative → toolchain/theme → guides → capability pages →
reference sync → README slim-down. Guides and capabilities can parallelize after IA.

## Breakdown / sub-specs

- [x] Docs IA + product narrative + glossary (project: Meta-Tools) — home story, nav map,
      concepts; locks dual-capability wording — SPEC-0142
- [x] MkDocs Material site toolchain + CI/theme (project: Meta-Tools) — `mkdocs.yml`,
      build/serve, Material config, deploy or `site/` artifact — SPEC-0143
- [x] Guides: getting started + time-tracking + idea→ship + outbound (project: Meta-Tools) — SPEC-0144
- [x] Capability showcase pages for major CLI surfaces (project: Meta-Tools) — report,
      ideas/next, tui, hub, projects/outbound, sheet, clock, completion, release-archive — SPEC-0145
- [x] Command reference synced to live CLI (project: Meta-Tools) — curated index or
      generated stubs; kill stale README command table — SPEC-0146
- [x] Root README slim front door + redirects into the site (project: Meta-Tools) — SPEC-0147

Sequencing: children 1→2 first; 3 and 4 in parallel after 2; 5 after 4 (or parallel with
shared CLI inventory); 6 last so links resolve.

## Acceptance criteria

- [x] A newcomer can open the docs home page and see both capabilities with clear next
      steps (track time vs start an idea).
- [x] Guides cover day-1 install, weekly time report loop, and full idea→ship (internal
      and outbound) without reading SPECs.
- [x] Capability pages cover every top-level `wt` command group (or explicitly defer with
      a tracked follow-up).
- [x] Site builds with MkDocs Material (search + nav work locally).
- [x] Root README is ≤1 screen of product pitch + install + link to the site; no stale
      full command encyclopedia.
- [x] Specs/ledger remain lint-clean and linked from Contribute / Decisions — not deleted.

## Test plan

- **Integration:** `mkdocs build --strict` (or equivalent) in CI/local; spot-check nav
  links; glossary terms used in guides resolve.
- **Manual:** cold-reader walkthrough of getting-started + idea→ship guide; compare
  reference page to `wt --help` for drift.
- **Regression:** `uv run pytest` (spec lint / existing suite) stays green; no requirement
  that product Markdown live under `docs/specs/`.

## Rollout / sequencing

Ship toolchain early so later children land as Markdown PRs against a living site.
Publish locally first (`mkdocs serve`); optional GitHub Pages / Cloudflare later without
blocking content.

## Definition of done

- [x] All child specs `done` or `superseded`.
- [x] Integration test plan executed; site builds strict.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

None — MkDocs Material chosen for Python-repo fit; specs remain secondary (linked /
optional section), not the human home path.
