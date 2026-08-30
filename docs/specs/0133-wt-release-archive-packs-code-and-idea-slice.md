---
id: SPEC-0133
title: "wt release-archive packs code and idea slice"
status: done
owner: user
created: 2026-08-08
updated: 2026-08-08
kind: feature
parent: SPEC-0131
depends_on: [SPEC-0132]
milestone: "M7: release packaging"
source_idea: IDEA-240
tags: [release, export, git]
---

## Context

Child of [SPEC-0131](./0131-release-archive-meta-tools-idea-slice-with-git.md)
(IDEA-240). Depends on SPEC-0132 export. Pack git-tracked code + Meta-Tools idea slice into
one release tarball.

## Goals / Non-goals

**Goals**
- CLI `wt release-archive` producing `work-tracking-YYYYMMDD-<sha>.tar.gz` (or `-o PATH`).
- Contents: `git archive HEAD` tree under `work-tracking-<sha>/` plus
  `ideas/ideas.org` from export defaults `--project Meta-Tools --all`.
- No XDG data, `.venv`, or untracked blobs.

**Non-goals**
- Implementing the export library (SPEC-0132).
- Import/restore.
- Multi-project default slices.

## Decision

Stage in a temp directory: extract `git archive --prefix=work-tracking-<sha>/` of `HEAD`,
write `ideas/ideas.org` via SPEC-0132 export with Meta-Tools `--all`, then compress the
prefix tree. Optional `--project` override; default remains Meta-Tools.

## Design

- [`src/wt/release_archive.py`](../../src/wt/release_archive.py) + `wt release-archive` in
  [`src/wt/cli.py`](../../src/wt/cli.py).
- Require a git checkout (fail clearly if not).
- Calls `export_idea_subtrees` directly.

## Acceptance criteria

- [x] `wt release-archive -o PATH` creates a gzip tarball.
- [x] Tarball contains `src/`, `docs/specs/`, and `ideas/ideas.org`.
- [x] `ideas/ideas.org` contains only Meta-Tools ideas under default flags.
- [x] Tarball does not contain `.venv`, `example-console*.tar.gz`, or XDG paths.
- [x] Export used for the slice is non-destructive to live org.

## Test plan

- **Automated:** `tests/test_idea_export.py::test_release_archive_members`.
- **Manual:** `wt release-archive -o …`; `tar -tzf` and open `ideas/ideas.org`.
- **Regression:** plain `git archive` behavior unchanged (this command is additive).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; tests pass.
- [x] Spec + ledger updated; `spec_lint` 0.

## Open questions

(none)
