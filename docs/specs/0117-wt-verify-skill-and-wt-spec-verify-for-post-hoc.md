---
id: SPEC-0117
title: "wt-verify skill and wt spec verify for post-hoc DoD"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
kind: feature
milestone: "M5: interactive desk"
source_idea: IDEA-193
tags: [skills, specs, dod, workflow]
---

## Context

Promoted from `IDEA-193`. AGENTS.md mandates a Definition of Done, but the skill pipeline
stops at implement/export/rework — nothing walks an agent through **post-hoc verification**
that a spec was closed honestly. `spec_lint` and `wt spec reconcile` are adjacent but do not
check AC checkboxes, Test plan presence, or epic child rollup.

## Goals / Non-goals

**Goals**
- Skill `wt-verify`: playbook that runs mechanical checks then forces human/agent judgment
  for “AC actually true”, “tests executed”, “body matches shipped”.
- CLI `wt spec verify <ID>` for checkable facts (internal `SPEC-NNNN`); `--json`, `--strict`
  (non-zero exit on failed mechanical checks). Report-only — never mutates status.
- Epic mode: children with `parent:` must be `done`/`superseded`; Breakdown unchecked boxes
  flagged.
- Wire into `wt skills install`, `EXPECTED_SKILLS` tests, WORKFLOW / orient mentions.

**Non-goals**
- Auto-marking specs `done` or rewriting AC checkboxes.
- Replacing AGENTS.md DoD prose.
- Making `wt spec verify` understand outbound ids (portable audit is skill Procedure B).
- Embedding full pytest inside the CLI by default (skill says run `uv run pytest`).

## Decision

Ship a **global** skill **`wt-verify`** (installed everywhere via `wt skills install`) as the
single post-hoc DoD playbook, plus CLI **`wt spec verify`** as the *internal* mechanical
backend. The skill branches: `SPEC-NNNN` in wt → CLI + ledger; outbound portable in a target
repo → file-based audit (no CLI). Default CLI report is read-only; `--strict` exits non-zero
on mechanical fail. Judgment items are attested in the skill, not scored by the CLI.

`/wt-implement-spec` remains the outbound **implement** path and hands off to `/wt-verify`
to close the loop — it is not a separate verify skill.

## Design

### CLI (`wt spec verify`)

- Resolve internal spec via existing `_find_spec`.
- Emit checks (pass/fail/warn/skip) covering at least:
  - frontmatter `status` present
  - `## Acceptance criteria` exists; if `status` is `done`/`in-progress`, no unchecked `- [ ]`
    AC bullets (empty AC section = fail for feature; epics may use Breakdown instead)
  - `## Test plan` non-empty (fail if missing/placeholder-ish `<…>` only)
  - `## Open questions` has no unresolved prose bullets starting with `-` that look open
    (best-effort warn), or section says `(none)`
  - epic: every child (`parent: this id`) status ∈ {done, superseded}; Breakdown unchecked
    count → fail/warn when status is `done`
- `--json` → `wt.spec.verify.v1` envelope `{schema, id, ok, checks[], judgment[]}`.
- `--strict` → exit 1 if `ok` is false.
- Outbound id → clear error pointing at `/wt-verify` Procedure B (portable) in the target
  repo — not at `/wt-implement-spec` as the verify skill.

### Skill (`skills/wt-verify/SKILL.md`)

**Global** playbook (SPEC-0017): installed into `~/.claude/skills` for every session/repo.
Branches on context:

- **A — Internal:** `SPEC-NNNN` → `wt spec verify` → pytest / manual → judgment → ledger /
  `status: done`.
- **B — Outbound portable:** `EXAMPLE-…` etc. in the target repo → audit the portable markdown
  (AC/Test plan/clock/outcome); never call `wt spec verify`.

Do **not** mark the skill “internal-only” — that conflates the skill with the CLI. The CLI is
internal-only; the skill is universal.

### Module

`src/wt/verify.py` (or `specs.verify_spec`) — pure library used by CLI; unit-tested with
temp spec files.

## Alternatives considered

- **Skill-only** — rejected; mechanical checks belong in CLI for agents/CI.
- **Mutating verify that flips status** — rejected; honesty stays with the authxx.
- **Name wt-close / wt-done-check** — rejected; `wt-verify` matches audit intent.

## Acceptance criteria

- [x] `wt spec verify SPEC-NNNN` prints a mechanical checklist; `--json` is `wt.spec.verify.v1`.
- [x] `--strict` exits non-zero when mechanical checks fail; default report does not write files.
- [x] Epic verify flags unfinished children / open Breakdown boxes when applicable.
- [x] Outbound ids are refused by the CLI with a pointer to `/wt-verify` (portable branch).
- [x] `skills/wt-verify/SKILL.md` is the global verify playbook (internal + outbound branches);
      listed in skill tests / `wt skills install`.
- [x] WORKFLOW (and orient) mention `/wt-verify` as the post-build close-the-loop step for
      both internal and outbound.
- [x] I can run `wt spec verify` on a known-good `done` spec and see `ok: true` (or only
      judgment leftovers).
- [x] I can use `/wt-verify` on an outbound portable (e.g. EXAMPLE-…) without being told to use
      a different verify skill.

## Test plan

- **Automated tests:** temp specs covering pass/fail AC, missing Test plan, epic children,
  outbound refusal, `--strict` exit code, JSON schema key.
- **Manual verification:** `wt spec verify SPEC-0117` (this spec) after implement; `wt skills
  list` shows `wt-verify`.
  Performed 2026-08-04: verify ok; skills list includes wt-verify.
- **Regression guard:** `tests/test_skills.py` EXPECTED_SKILLS updated; full `uv run pytest`.

## Clock Log

(use `wt idea clock-in/out` on IDEA-193)

## Rollout / migration

Additive. No data migration. Install skills after merge: `wt skills install`.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — resolved on IDEA-193)
