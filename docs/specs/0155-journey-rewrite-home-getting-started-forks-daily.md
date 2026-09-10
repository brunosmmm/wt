---
id: SPEC-0155
title: "Journey rewrite: home, getting-started forks, daily/weekly guides"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0153
tags: [docs]
depends_on: [SPEC-0153, SPEC-0154]
source_idea: IDEA-393
---

## Context

Child of SPEC-0153. Home and getting-started still lead with idea-pipeline framing and
empty-time risk. Auditors asked for day-shaped operating guides and forks (time / idea /
agent).

## Goals / Non-goals

**Goals**

- Rewrite `docs/product/index.md` and `guides/getting-started.md` with clear forks.
- Add **daily** and **weekly** operating guides embedding Wave A/B SVGs from SPEC-0154.
- Fold useful capability-page embeds left open on SPEC-0148 into this journey work.

**Non-goals**

- New capture toolchain (0154).
- Full architecture/agent/outbound deep guides (0156–0158).

## Decision

Journey-first docs: first viewport sells dual product with real dashboard + ideas shots;
getting-started offers three short paths; daily/weekly pages are the human operating
rhythm (agenda → tasks → hub/next → report/review).

## Design

- `docs/product/index.md` — hero dual claim + embedded `cli-wt-dashboard` + `cli-ideas`/`cli-next`.
- `guides/getting-started.md` — forks: track time / triage ideas / agent JSON.
- `guides/daily-ops.md`, `guides/weekly-ops.md` (names flexible) — embed agenda/tasks/report/review/hub.
- `mkdocs.yml` nav updates; mkdocs strict.

## Acceptance criteria

- [x] Home shows time + ideas SVGs in the first screenful of content.
- [x] Getting-started has explicit time / idea / agent forks.
- [x] Daily and weekly guides exist, linked from guides index, embed ≥3 Wave A/B SVGs total.
- [x] `mkdocs build --strict` passes.

## Test plan

- **Automated:** string/path asserts in `tests/test_docs_captures.py` or a small docs test;
  mkdocs strict in CI/dev.
- **Manual:** browse home + new guides on docs serve.
- **Regression:** prior guide tests still green.

## Definition of done

- [x] AC met; test plan executed; ledger updated; IDEA-393 reconciled.

## Open questions

- None.


## Shipped notes

Home embeds dashboard + ideas SVGs. Getting started has Paths A/B/C (time / ideas / agent).
Added `guides/daily-ops.md` and `guides/weekly-ops.md` with Wave A/B embeds; nav + guides
index updated. Report / tasks-agenda / hub capability pages embed representative shots.
`mkdocs build --strict` and docs capture tests green.
