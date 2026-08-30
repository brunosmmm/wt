---
id: SPEC-0038
title: YAML-safe scaffold titles and hyphenated org tag parsing
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [specs, org, bugs]
depends_on: [SPEC-0013, SPEC-0015, SPEC-0005]
---

## Context

Promoting `IDEA-045` (`wt spec new --from-idea`) wrote an outbound draft whose
`title:` line included a trailing org tag cookie `:session-triage:`. Unquoted YAML + colon
→ `yaml.ScannerError` when regenerating the outbox index — promote looked crashed even though
the file existed.

Root causes:
1. **orgparse** strips tags with `RE_HEADING_TAGS = r'(.*?)\s*:([\w@:]+):\s*$'`, which does
   **not** allow hyphens. Tags like `session-triage` stay inside `node.heading` and
   `node.tags` stays empty. (Emacs Org allows `-` in tags.)
2. Scaffold writes `title: {title}` **unquoted**, so any `:` in the title (embedded tag *or*
   prose like `cross-navigation: from…`) breaks frontmatter.

## Goals / Non-goals

**Goals**
- Parse hyphenated (and otherwise Org-legal) trailing tag cookies into `Task.tags` and strip
  them from `Task.heading`.
- Scaffold internal + outbound `title:` as a YAML-safe quoted scalar.
- Promote/index regen succeeds for ideas tagged `:session-triage:` and titles containing `:`.

**Non-goals**
- Patching/vendoring orgparse itself.
- Rewriting existing org files on disk (parse-time normalization only).
- Expanding `known_epics` to outbound ids (separate issue).

## Decision

In `_node_to_task`, re-apply a hyphen-aware trailing-tag parse on the heading (union with
orgparse's tags). In scaffolders, emit `title:` via `json.dumps` (always double-quoted).

## Design

Shipped:
- `org._heading_and_tags` / `_RE_HEADING_TAGS` with `[\w@:-]+`
- `specs._yaml_fm_value` used for `title:` in `scaffold_from_idea` + `scaffold_outbound`
- Tests in `test_ideas` / `test_export` / `test_promote`

## Alternatives considered

- **Normalize tags to underscores on write** — rejected; breaks user-facing tag names.
- **Quote only when `:` present** — rejected; always-quote is simpler and test-stable.
- **Monkeypatch orgparse.RE_HEADING_TAGS** — fragile across versions; local re-parse is enough.

## Acceptance criteria

- [x] `add_idea(..., tags=("session-triage",))` → `task.tags` contains `session-triage` and
      heading has no trailing cookie.
- [x] Scaffold title containing `:` yields parseable frontmatter; `write_outbox_index` does not
      raise.
- [x] Existing untagged scaffolds still lint/validate.
- [x] Tests + full pytest green; ledger/lint clean.

## Test plan

- **Automated:** hyphen tag + quoted colon title + index regen. ✓
- **Manual:** N/A.
- **Regression:** `uv run pytest`.

## Rollout / migration

No on-disk org rewrite. Existing headlines with embedded `:hyphen-tag:` start parsing correctly
on next load.

## Definition of done

- [x] Acceptance criteria met; test plan executed.
- [x] Spec matches shipped; ledger regenerated; `spec_lint` exits 0.

## Open questions

_None._
