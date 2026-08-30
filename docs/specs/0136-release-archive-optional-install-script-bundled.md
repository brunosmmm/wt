---
id: SPEC-0136
title: "Release archive optional install script points wt at bundled ideas/"
status: done
owner: user
created: 2026-08-30
updated: 2026-08-30
source_idea: IDEA-292
milestone: "M7: release archive"
tags: [release, config, ideas]
depends_on: [SPEC-0131, SPEC-0133]
---

## Context

Promoted from `IDEA-292`. After extracting a `wt release-archive` tarball, default XDG
config still points at `~/work/org`, so `uv run wt ideas` shows 0 ideas even though the
tree ships `ideas/ideas.org`. Operators need an *optional* install step to wire config at
the extracted checkout.

> Reconstruct note: this file was missing from a release-archive export while the idea
> remained `SPECCED` with `:SPEC: SPEC-0136`. Body matches the shipped script + idea Log.

## Goals / Non-goals

**Goals**

- Ship `scripts/install-bundled-config.sh` in-repo (and in the release tarball).
- Script resolves `ROOT` from its path; merges/writes XDG `config.yaml` so `org_files`,
  `org_ideas_file`, and `specs_dir` point at the extracted tree; backs up an existing
  config before overwrite/merge.
- Prints next steps (`uv sync`, `wt ideas --all`).

**Non-goals**

- Silent overwrite without backup.
- Changing default config for non-release installs.

## Decision

Optional operator-run script; absolute paths into the release tree; backup then merge
via PyYAML when available, else minimal stub.

## Design

- `scripts/install-bundled-config.sh` — as shipped.
- `release_archive` copies the script into the tarball (SPEC-0133).

## Acceptance criteria

- [x] Script exists and merges/writes the three keys against the checkout.
- [x] Existing `config.yaml` is backed up before change.
- [x] Release-archive packaging includes the script.

## Test plan

Executed at ship time per IDEA-292 Log (script + packaging). Reconstruct: file present;
`bash -n scripts/install-bundled-config.sh`.

## Definition of done

- [x] AC met; idea Log records ship.

## Open questions

_(none)_
