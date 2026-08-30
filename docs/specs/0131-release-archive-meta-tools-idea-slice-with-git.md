---
id: SPEC-0131
title: "Release archive: Meta-Tools idea slice with git code"
status: done
owner: user
created: 2026-08-08
updated: 2026-08-08
kind: epic
milestone: "M7: release packaging"
source_idea: IDEA-237
tags: [release, export, ideas, archive]
---

## Context

Promoted from `IDEA-237` after explore locked slice scope and bundle shape. A code-only
`git archive` of wt omits the Meta-Tools idea corpus that documents *why* shipped SPECs
exist. Live `ideas.org` / archive mix all projects, so a release bundle must **filter**, not
dump.

Related but distinct: sheets sync (SPEC-0123), ideas.org rotation (SPEC-0070/0071), CLI
`--json` (SPEC-0026).

## Goals / Non-goals

**Goals**
- Read-only export of filtered idea *subtrees* as a portable org file (reuse `wt ideas`
  filter vocabulary).
- One release tarball: git-tracked code + `ideas/ideas.org` Meta-Tools slice (`--all`).
- Non-destructive: export never moves or deletes live org.

**Non-goals**
- New filter DSL / second vocabulary.
- Dumping XDG `data_dir`, mappings, org-backups, meetings.jsonl.
- Import/restore of an exported slice in v1.
- Changing lifecycle `archive_idea` behavior.
- Including non–Meta-Tools ideas in the default release archive.

## Decision

Ship an epic:

1. **Export:** library + `wt ideas export` — select via existing filters; copy subtrees
   (same span as `archive_idea`, no delete); write one org file.
2. **Release archive:** `wt release-archive` — `git archive HEAD` + default
   `--project Meta-Tools --all` slice under `ideas/ideas.org` in one `.tar.gz`.

## Architecture / cross-cutting design

```
collect_idea_tasks(filters) → copy subtrees → ideas/ideas.org
git archive HEAD            → code tree
                            → single release tarball
```

**Invariants**
- Filter vocabulary = `wt ideas` / `collect_idea_tasks` (no parallel DSL).
- Default release slice = Meta-Tools + `--all` (open + done/archived sources already in
  `org_files`).
- Export is read-only; source org unchanged.
- Deduplicate by `:ID:` if the same idea appears across rotated/archive files.
- Tarball must not include `.venv`, live XDG data, or untracked blobs.

## Breakdown / sub-specs

- [x] [SPEC-0132](./0132-filtered-idea-subtree-export.md) — Filtered idea subtree export
      (IDEA-239)
- [x] [SPEC-0133](./0133-wt-release-archive-packs-code-and-idea-slice.md) —
      `wt release-archive` packs git code + Meta-Tools idea slice (IDEA-240; depends_on 0132)

Sequencing: **0132 → 0133**.

## Acceptance criteria

- [x] Operators can export Meta-Tools `--all` ideas to an org file without mutating live org.
- [x] `wt release-archive` produces a tarball containing code + `ideas/ideas.org` with only
      Meta-Tools ideas.
- [x] Other projects' ideas are absent from the default release slice.
- [x] All child specs `done` or `superseded`.

## Test plan

- **Integration:** `tests/test_idea_export.py` covers export filter + release member list.
- **Manual:** run `wt release-archive -o …`; inspect tarball; open `ideas/ideas.org`.
- **Regression:** existing `wt ideas` / `archive_idea` tests unchanged in behavior.

## Rollout / sequencing

Accepted epic + children; implemented export → release-archive; rebuild human release
tarball with `wt release-archive`.

## Definition of done

- [x] All child specs `done` or `superseded`.
- [x] Integration test plan executed; new tests green.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

(none — locked on IDEA-237)
