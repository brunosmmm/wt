---
id: SPEC-0095
title: "Skill/CLI: detect multi-project conversations and fan-out ideas/specs"
status: done
owner: user
created: 2026-07-29
updated: 2026-07-29
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-117
tags: [skills, projects, routing, explore]
---

## Context

Agents collapse multi-repo conversations into one idea / one `research.root` (SPEC-0042),
even when several already-tracked projects are named (Example + PFW-Intelligence/example-console +
a configured outbound project + an unconfigured path like `~/work/other-repo`). Dispositions (IDEA-117):
skills + CLI map; warn+ask for unknown paths; fan-out as epic + seed-children; soft warn on
multi-project (continue); require project-map preview before Summary.

## Goals / Non-goals

**Goals**
- `wt projects --json` → `wt.projects.v1` agent map (name, topic count, research, outbound).
- Skills (`wt-orient`, `wt-seed`, `wt-explore`, `wt-capture`, `wt-new-work`) teach multi-project
  detection, project-map preview, epic fan-out, and warn+ask for unknown paths.
- WORKFLOW.md notes the gate.

**Non-goals**
- Inventing projects not in the map; auto-promoting N specs; changing single-valued
  `research` on `wt idea show`; hard-blocking explore when ≥2 projects named.

## Decision

- **CLI:** `wt projects --json` emits every known routing name = `known_projects` ∪
  `outbox_targets` keys ∪ `Meta-Tools`, each with `resolve_research_context` + topic count +
  `outbound` bool when in outbox.
- **Skills:** before Summary (seed/explore), if chat names ≥2 map hits (project name or
  `research.root` path), agent must preview a project map and propose an **epic umbrella +
  per-project child ideas** (`seed-children` after epic accept). Soft-warn if continuing a
  single-root explore anyway. Paths not in the map → warn and ask (do not invent
  `outbox_targets`).
- Rich `wt projects` unchanged (mappings-only list stays for humans).

## Design

- `rules.projects_payload` → `wt.projects.v1`; CLI `--json` on `wt projects`
- Skill “Multi-project gate” in orient/seed/explore/capture/new-work; WORKFLOW note
- Tests: `tests/test_projects_json.py`

## Alternatives considered

- Skills-only — rejected (1B needs agent-readable map).
- Hard refuse single-root — rejected (4B soft warn).
- N sibling ideas without epic — rejected (3B epic + children).

## Acceptance criteria

- [x] `wt projects --json` schema `wt.projects.v1` lists union of mappings + outbox + Meta-Tools
      with research + outbound.
- [x] Skills require project-map preview before Summary when ≥2 projects/paths named; prescribe
      epic + children fan-out; soft-warn if single-root continues; warn+ask for unknown paths.
- [x] Rich `wt projects` still works; no silent inventing of projects.
- [x] Tests cover JSON envelope + outbox/research fields.

## Test plan

- **Automated:** projects JSON with mappings + outbox entry + Meta-Tools research.
  **Executed 2026-07-29:** `uv run pytest tests/test_projects_json.py tests/test_assoc.py`
  — 18 passed.
- **Manual:** `wt projects --json | jq` against live config; skim skill diffs.
- **Regression:** `tests/test_assoc.py` projects CLI.

## Rollout / migration

Additive `--json`. Agents pick up skills after `wt skills install` / symlink refresh.

## Definition of done

- [x] AC met; tests pass; ledger updated.

## Open questions

(none — IDEA-117 dispositions locked)
