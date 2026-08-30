---
id: SPEC-0051
title: "Align skills and help with CLI reality"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
parent: SPEC-0050
tags: [skills, docs, ergonomics]
source_idea: IDEA-041
depends_on: [SPEC-0017, SPEC-0021, SPEC-0041, SPEC-0045]
---

## Context

Promoted from `IDEA-041` (epic SPEC-0050). Playbooks still claim outbound `wt spec generate`
and `docs/outbox/` paths after SPEC-0041/0021 fixed the CLI. Agents treat skills as contract.

## Goals / Non-goals

**Goals**
- Skills + high-traffic CLI help match current behavior.
- Test guards against regression of the worst stale phrases.
- Document Cursor dual-install via `--dest` without changing default `~/.claude/skills`.

**Non-goals**
- New CLI enforcement (outbound generate already hard-fails).
- Rewriting historical done specs (e.g. SPEC-0017 body) — fix live skills/docs only.
- Changing default skills install destination.

## Decision

Doc/skill alignment PR: fix `wt-generate`, `wt-export`, related WORKFLOW/README blips, and
`wt spec new --target` help/docstrings that still say `docs/outbox/`. Add pytest grep guards
on `skills/`.

## Design

### Skill edits
- `skills/wt-generate/SKILL.md`: internal `SPEC-NNNN` only; outbound → export /
  `wt-implement-spec`.
- `skills/wt-export/SKILL.md`: data-dir outbox (`<data_dir>/outbox/<project>/` or
  “wt outbox”), not `docs/outbox/`.
- `skills/wt-new-work` / `wt-orient`: confirm outbound accept ≠ `--write-ledger`.
- WORKFLOW skills section: note `wt skills install --dest …` for Cursor if needed.

### CLI / code comments
- `src/wt/cli.py` `--target` help and `spec new` docstring.
- Light docstring fixes in `specs.py` / `export.py` module headers where they still say
  `docs/outbox/` (behavior unchanged).

### Tests
- `tests/test_skills.py`: assert no `docs/outbox` under `skills/`; `wt-generate` body must
  not instruct generating outbound / `PROJ-` ids.

## Alternatives considered

- **Change default install to Cursor path** — rejected (SPEC-0045 non-goal; Claude default OK).
- **Leave skills stale** — rejected; agents trust them.

## Acceptance criteria

- [x] `wt-generate` documents internal-only generate; points outbound to export/implement.
- [x] No `docs/outbox` path claims in `skills/*.md`.
- [x] CLI `--target` / spec-new help no longer says `docs/outbox/` as the live store.
- [x] WORKFLOW notes optional `--dest` for non-Claude skill hosts.
- [x] Automated grep/guards in `tests/test_skills.py` green.

## Test plan

- **Automated:** extended `tests/test_skills.py`; full pytest — **executed, green**.
- **Manual:** `wt skills list`; skim `wt spec new --help` — help shows `<data_dir>/outbox/`.
- **Regression:** skill frontmatter/EXPECTED_SKILLS unchanged except text.

## Rollout / migration

None. Re-`wt skills install` picks up symlink text immediately.

## Definition of done

- [x] AC met; ledger updated.

## Open questions

_None._
