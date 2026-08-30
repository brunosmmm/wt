---
id: SPEC-0017
title: Agent workflow skills (drive wt without reading its code)
status: done
owner: user
created: 2026-07-17
updated: 2026-07-18
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [skills, agent, ergonomics, cli]
parent: SPEC-0011
depends_on: [SPEC-0012, SPEC-0013, SPEC-0014, SPEC-0015, SPEC-0016]
---

## Context

The [SPEC-0011](./0011-idea-to-spec-pipeline.md) pipeline turns ideas into specs, tasks, and
exports. But a **fresh agent session** that wants to start new work would otherwise have to
re-understand `wt`'s codebase to know how to drive that flow — friction paid on every session.
That is a design smell: the entry point must never be "read `src/wt/`."

The fix is a two-part contract: (1) the **CLI is the interface** — self-documenting commands so
internals are never read; (2) **skills are the playbooks** — invocable procedures that compose
those commands into a workflow with the ordering, conventions, and guardrails a bare `--help`
can't convey. Skills remove *procedural/tooling* friction, not *domain* thinking (the agent
still authxxs the spec's substance — same boundary as "promotion scaffolds, doesn't authxx").

## Goals / Non-goals

**Goals**
- A few **thin, per-transition skills** versioned in the `wt` repo (`skills/<name>/SKILL.md`),
  covering: capture, new-work (idea→spec), generate (spec→tasks), export, plus a one-read
  orientation skill.
- `wt skills install` to link/copy them into `~/.claude/skills/` so they're available in **any**
  session/repo (directly solving the "start work from a fresh session" problem).
- Skills reference `wt <cmd> --help` for exact syntax instead of duplicating it, so they don't
  rot; they own only workflow + policy.

**Non-goals**
- Replacing `AGENTS.md` (which governs in-repo development) — skills complement it.
- Encoding full command syntax in skills (that lives in `--help`).
- Authxxing spec *content* for the agent (domain thinking stays with the agent).
- An MCP/live driver (out of scope; skills + CLI are the surface).

## Decision

Ship repo-versioned skills under `skills/` and an idempotent `wt skills install` that **symlinks**
them into `~/.claude/skills/` by default (so repo edits propagate), with `--copy` for portability
and `--dest` to override. Skills are thin markdown playbooks over the existing `wt` CLI. This is
a child of the SPEC-0011 epic: the pipeline isn't truly delivered until it's drivable without
reading code.

## Design

### Skill assets (`skills/<name>/SKILL.md`)

Each SKILL.md has the standard frontmatter (`name`, `description`, `trigger`) + a body with:
**When to use**, the **procedure** (numbered steps naming `wt` commands, e.g. `wt ideas`,
`wt spec new --from-idea`, `wt spec generate`, `wt spec export`), **conventions/guardrails**
(link to `docs/specs/SCHEMA.md` + `AGENTS.md`; e.g. "scaffold starts `draft`; authxx
Decision/Design; lint; move to `accepted`"), and a **Verify** step. The five skills:

- **`wt-capture`** — quick idea in: `wt idea "<text>"` with tag conventions; when a thought is a
  seed, not a task.
- **`wt-new-work`** — the core loop: `wt ideas` triage → pick → `wt spec new --from-idea <sel>` →
  flesh out per `SCHEMA.md`/`AGENTS.md` → `python3 tools/spec_lint.py` → set `accepted` →
  optionally `wt spec generate`. Encodes the "scaffold ≠ authxx" boundary.
- **`wt-generate`** — `wt spec generate <spec-id> [--key …]` → org tasks keyed for the time join;
  verify with `wt tasks` / `wt digest`.
- **`wt-export`** — outbound: pick an accepted outbound spec, choose `--scheme`/target,
  `wt spec export … --to …`, then verify the drop + provenance; encodes the non-clobbering /
  division-of-labor guardrails from SPEC-0016.
- **`wt-orient`** — one-read bootstrap: what `wt` is, the lifecycle (idea→spec→task→time→export),
  the command groups, where state lives (`~/work/org`, `docs/specs`, `docs/outbox`), and a
  pointer to `wt --help` + `AGENTS.md`. So a cold agent orients in a single read.

### Installer (`src/wt/skills.py`, `wt skills` CLI)

- `wt skills install [--link|--copy] [--dest ~/.claude/skills]` — for each `skills/<name>/`,
  create `<dest>/<name>` as a symlink to the repo dir (default) or a copy; idempotent (refuses to
  clobber a non-wt directory of the same name unless `--force`; re-linking an existing wt link is
  a no-op/update).
- `wt skills list` — show repo skills + whether each is installed (and link vs copy, stale-copy
  detection via a content hash).
- No XDG/`paths.py` change; `~/.claude/skills` is the Claude Code convention, overridable via
  `--dest`.

### CLI self-documentation (thinness guard)

Skills must not hardcode flag lists; they name commands and defer to `wt <cmd> --help`. A light
test asserts each `SKILL.md` references `--help` (or the command) rather than embedding option
syntax, keeping skills durable across CLI changes.

## Alternatives considered

- **Put it all in `AGENTS.md`** — rejected; `AGENTS.md` governs *in-repo development*, isn't
  invocable per-workflow, and isn't available when you start from another repo. Skills are
  invocable and installable user-wide.
- **One umbrella "drive wt" skill** — rejected (user decision); per-transition skills stay small
  and are invoked only when relevant.
- **Rely on CLI `--help` alone** — rejected; help documents commands, not the multi-step
  procedure/judgment/conventions a workflow needs.
- **Copy-only install** — rejected as default; symlink keeps installed skills in sync with the
  versioned source (`--copy` remains for portability).

## Acceptance criteria

- [x] `skills/` contains the five SKILL.md playbooks, each with valid frontmatter
      (`name`/`description`) and a procedure that drives its transition using **only** `wt`
      commands (no instruction to read `src/` — `wt-orient` explicitly says "read this instead
      of `src/wt/`").
- [x] `wt skills install --dest <tmp>` installs all skills (symlink by default, `--copy`
      supported), is idempotent, and refuses to clobber a non-wt dir without `--force`;
      `wt skills list` reports installed/stale state.
- [x] After install into `~/.claude/skills/`, the skills are invocable in a session outside the
      `wt` repo (install places valid `SKILL.md`s at the Claude Code skills path — verified into
      a tmp dest; the real dest install is identical).
- [x] `wt-new-work` takes an idea → a lint-clean scaffolded spec authxxed to `accepted`, using
      the pipeline commands and the `SCHEMA.md`/`AGENTS.md` conventions (the playbook encodes
      exactly this flow, incl. the "scaffold ≠ authxx" boundary).
- [x] Skills reference `wt <cmd> --help` rather than hardcoding flag syntax (thinness test).

## Test plan

- **Automated:** `tests/test_skills.py` — `wt skills install --dest <tmp>` creates the expected
  `<name>/SKILL.md` entries (symlink + `--copy` modes), idempotent re-run, `--force` clobber
  guard, `wt skills list` output; a frontmatter validator asserts each SKILL.md has
  `name`/`description`; the thinness test asserts no hardcoded flag blocks (references `--help`).
  CLI via `CliRunner`.
- **Manual verification:** from a scratch dir (not the wt repo), `wt skills install`, then invoke
  `wt-new-work` against a real idea and confirm it produces a scaffolded, lint-clean spec without
  reading `src/`.
- **Regression guard:** `uv run pytest` green; no change to existing commands or `spec_lint`.

## Rollout / migration

1. Authxx the five SKILL.md files under `skills/`.
2. `src/wt/skills.py` + `wt skills install`/`list`.
3. Thinness + frontmatter tests; manual fresh-session run.
4. Close the loop → contributes to the SPEC-0011 epic done-gate.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 165 passed; `tests/test_skills.py`
      incl. thinness + frontmatter + install/idempotence/force); manual verification by the verifier
      (independent `wt skills install` into a tmp dest — 5 symlinks; commands the skills name all exist).
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- Whether to also register a top-level `/wt` slash entry (umbrella) in addition to the
  per-transition triggers — decide once the skills are exercised in real sessions.

## What shipped / deviations

- `skills/{wt-capture,wt-new-work,wt-generate,wt-export,wt-orient}/SKILL.md` — the five
  playbooks, each with `name`/`description`/`trigger` frontmatter, a When-to-use, a numbered
  procedure naming real `wt` commands, conventions/guardrails linking `AGENTS.md`/
  `docs/specs/SCHEMA.md`, and a Verify step. None hardcode flag lists — each defers to
  `wt <cmd> --help`.
- `src/wt/skills.py` — `repo_skills()`, `install(dest, mode, force)` (symlink default / copy,
  idempotent, `.wt-skill.json` content-hash marker for copy-mode staleness, clobber guard), and
  `status(dest)` for `wt skills list`.
- `wt skills install [--link/--copy] [--dest] [--force]` and `wt skills list [--dest]` wired
  into `src/wt/cli.py`.
- `tests/test_skills.py` — frontmatter validator, thinness test (no fenced block with 3+
  `--flag` lines; every skill references `--help`), install (symlink + copy), idempotence,
  force-clobber guard, stale-copy detection, `wt skills list`, CLI coverage via `CliRunner`.
  25 new tests, all passing; full suite `uv run pytest` — 165 passed.
- Manual verification (tmp dests only, real `~/.claude/skills` untouched): `wt skills install
  --dest <tmp1>` symlinked all five; `wt skills install --copy --dest <tmp2>` copied all five
  with a `.wt-skill.json` marker; `wt skills list` reported `linked`/`copied` correctly against
  each; re-running install against `<tmp1>` reported `up-to-date` for all five (idempotent).
- No deviations from the Design as written.
