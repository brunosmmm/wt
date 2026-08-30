---
id: SPEC-0132
title: "Filtered idea subtree export"
status: done
owner: user
created: 2026-08-08
updated: 2026-08-08
kind: feature
parent: SPEC-0131
milestone: "M7: release packaging"
source_idea: IDEA-239
tags: [ideas, export, org]
---

## Context

Child of [SPEC-0131](./0131-release-archive-meta-tools-idea-slice-with-git.md)
(IDEA-239). First slice: read-only export of filtered idea subtrees as a portable org file.

## Goals / Non-goals

**Goals**
- Library: select ideas via `collect_idea_tasks` filters; copy top-level subtrees; write org.
- CLI: `wt ideas export` with the same filter flags as `wt ideas`, plus `-o` / `--dry-run`.
- Deduplicate by `:ID:`; stable order by idea id.
- Non-destructive (source org unchanged).

**Non-goals**
- Release tarball packaging (SPEC-0133).
- New filter vocabulary.
- Import/restore.

## Decision

Reuse `collect_idea_tasks` for selection. For each task, copy the headline through the line
before the next top-level `*` headline (same span as `archive_idea`), without deleting from
the source. Emit one org file: `#+TODO:` from `org_idea_keywords` + concatenated subtrees.
`wt ideas` is an IdeasGroup that defaults to `list` so existing `wt ideas --json` keeps working;
`export` is an explicit subcommand.

## Design

- Module: [`src/wt/idea_export.py`](../../src/wt/idea_export.py).
- `export_idea_subtrees(cfg, path, **filters) -> list[str]` (ids written).
- CLI: `wt ideas export` under IdeasGroup in [`src/wt/cli.py`](../../src/wt/cli.py).
- `--dry-run`: print count + ids, no write.

## Acceptance criteria

- [x] `wt ideas export --project Meta-Tools --all -o PATH` writes only Meta-Tools ideas.
- [x] Source `ideas.org` / archive files are byte-unchanged by export.
- [x] Exported file loads via `load_tasks` when used as `org_ideas_file`.
- [x] `--dry-run` lists ids without writing.
- [x] Foreign-project ideas in the same corpus are excluded when filtered.

## Test plan

- **Automated:** `tests/test_idea_export.py` — filter, non-mutation, dry-run, parse round-trip,
  CLI export + list regression.
- **Manual:** export live Meta-Tools slice via `wt release-archive` / export CLI.
- **Regression:** `archive_idea` still moves (not copies).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; tests pass.
- [x] Spec + ledger updated; `spec_lint` 0.

## Open questions

(none)
