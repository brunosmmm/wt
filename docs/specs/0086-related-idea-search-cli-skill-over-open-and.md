---
id: SPEC-0086
title: "Related-idea search: CLI + skill over open and closed ideas"
status: done
owner: user
created: 2026-07-28
updated: 2026-07-28
source_idea: IDEA-093
milestone: "M4: cli ergonomics"
kind: feature
tags: [cli, ideas, skills, search]
---

## Context

Promoted from `IDEA-093`. Before capturing or promoting, we need to find **related ideas that
already exist** — open *and* closed — without reading the whole org corpus by hand.

What exists today (measured during explore):

- `wt ideas --json` / `--all` is metadata-only (`wt.ideas.v1` rows: id, state, heading, tags,
  kind, project, next, stamps). No Summary / questions / Log.
- `wt idea show --json` is the only structured full-text surface — one idea per call.
- `resolve_selector` (`src/wt/org_write.py`) heading-substring fallback is a **single-match
  resolver**, not search: ambiguous → error; it also scans non-idea org tasks (live:
  `wt idea show related` mixed IDEA-093 with an inbox DONE headline).
- Tags and `FOLDED_INTO` / `SUPERSEDED_BY` are soft grouping / exit-time pointers, not discovery.
- Corpus (~105 ideas including archive) is already visible to `load_tasks` via `org_files`.
  In-process `read_idea_enrichment` ×105 ≈ 25ms; agent-side N× `wt idea show` is tens of
  seconds — so body search must live in-process, not in a skill shell loop.
- Body search matters: query `specref` → 1 heading hit, 3 hits once Summary/Log is included.

## Goals / Non-goals

**Goals**

- Ideas-only full-text search over heading + enrichment bodies, including closed/archived.
- Ranked structured JSON for agents; readable Rich table for humans.
- A thin skill that runs the search before capture / promote.
- Deterministic ranking (no embeddings).

**Non-goals**

- Semantic / embedding / LLM ranking.
- Changing `resolve_selector` (still the single-task picker; search is a separate surface).
- Replacing tag filters (`--kind` / tags stay; search ≠ filter).
- Indexing / SQLite / background refresh — corpus is small enough to scan.
- Searching non-idea org tasks.

## Decision

Add **`wt ideas --query TEXT`**: an ideas-only search mode on the existing list command.

- **Corpus:** `--query` implies open **and** closed (same as `--all`). `--state` / `--kind`
  still narrow. Explicit `--all` is redundant but harmless when querying.
- **Fields:** case-insensitive match over **heading + Summary + Open questions + Log**.
- **Ranking:** whitespace-tokenize the query; **AND** (every token must appear somewhere in
  the blob). Score = `3×heading_token_hits + 2×summary_token_hits + 1×(questions|log)_hits`.
  Higher score first; tie-break by existing freshness key.
- **JSON:** when `--query` is set, emit `wt.ideas.search.v1` — same row fields as
  `wt.ideas.v1` plus `score` and `snippet` (short excerpt around the first hit). Without
  `--query`, `wt.ideas.v1` is unchanged.
- **Skill:** new `wt-related` playbook; `wt-capture` / `wt-seed` / `wt-new-work` point at it.
- **Default limit:** 25 hits (`--limit N`; `0` = unlimited).

## Design

### Core (`src/wt/report.py`)

- `tokenize_idea_query(text) -> list[str]`
- `score_idea_match(tokens, heading, summary, questions, log) -> int | None` — `None` = miss
- `idea_match_snippet(...)` — ≤80 chars around the earliest token hit
- `search_idea_tasks(cfg, query, *, state=None, kind=None, limit=25) -> list[tuple[Task, int, str]]`
  — uses `collect_idea_tasks(..., all_done=True)` then enrichment via
  `explore.read_idea_enrichment`, scores, sorts, applies limit

### CLI (`src/wt/cli.py` → `ideas_cmd`)

- `--query TEXT`, `--limit INT` (default 25)
- When `query`: call search path; Rich table adds a `score` column; JSON uses search schema
- Help text documents that `--query` includes closed ideas

### Skill (`skills/wt-related/SKILL.md`)

- When: before `wt idea "…"` / `/wt-seed` / `/wt-new-work`, or when a thought might already
  exist
- Procedure: `wt ideas --query "…" --json` (exact flags via `--help`); inspect hits; only
  capture/promote if nothing close enough
- Thin: no hardcoded flag lists; defer to `--help`

### Docs touch

- `docs/WORKFLOW.md`: one line under triage / capture pointing at `wt ideas --query` /
  `/wt-related`
- `tests/test_skills.py` `EXPECTED_SKILLS` gains `wt-related`

## Alternatives considered

- **`wt idea search` subcommand** — clearer verb, but splits discovery from `wt ideas` filters
  agents already know. Lost to composing on the list command.
- **Skill-only over `wt ideas --json` headings** — fails the `specref` body-search measurement
  and scales poorly if the skill shells `show`.
- **Extend `resolve_selector` to return multi-match** — would break every caller that expects
  exactly one task; wrong abstraction.
- **Embeddings** — non-deterministic, extra deps; deferred.

## Acceptance criteria

- [x] `wt ideas --query TEXT` returns only ideas (`is_idea`), never inbox/non-idea tasks.
- [x] Closed/archived ideas are included under `--query` without requiring a separate mental
      model beyond "query searches the full idea corpus".
- [x] A token present only in Summary/Log can match (heading-only is insufficient).
- [x] Multi-token queries AND-compose; misses return an empty list (exit 0), not an error.
- [x] `--json` with `--query` emits `wt.ideas.search.v1` with `score` + `snippet` on each hit;
      without `--query`, `wt.ideas.v1` is unchanged.
- [x] `--kind` / `--state` still filter the search corpus; `--limit` caps hits (`0` = all).
- [x] `skills/wt-related/SKILL.md` exists, installs via `wt skills`, and is listed in the
      skills test set; capture/seed/new-work mention related search.
- [x] `resolve_selector` behavior is unchanged.

## Test plan

- **Automated tests:** `tests/test_idea_search.py`
  - heading hit, summary-only hit, multi-token AND miss/hit
  - closed (PROMOTED) idea is returned under `--query`
  - non-idea org headline with the same substring is **not** returned
  - JSON schema `wt.ideas.search.v1` + `score`/`snippet`; plain `wt ideas --json` still
    `wt.ideas.v1`
  - `--limit 1` caps; ranking puts heading-heavy score above body-only
  - `tests/test_skills.py`: `wt-related` in `EXPECTED_SKILLS` + thinness guards
- **Manual verification:**
  - `uv run wt ideas --query specref --json` includes IDEA-031 and body-only relatives
  - `uv run wt ideas --query related` does not error on multiple hits (unlike
    `wt idea show related`)
  - **Performed 2026-07-28:** `--query specref --json` → `wt.ideas.search.v1` with
    IDEA-031 (score 6), IDEA-037/032 body hits; `--query related` returned 7 ranked ideas
    (exit 0) while `wt idea show related` still reports ambiguous. `wt skills install`
    linked `wt-related`.
- **Regression guard:** `uv run pytest`; existing ideas/json/completion tests stay green.
  (Pre-existing failures unrelated to this change: `test_idea_state_color` ×2,
  `test_columns_env_var_controls_width_when_piped` — reproduce on clean `report.py`.)

## Clock Log

Prefer `wt idea clock-in` / `clock-out` on IDEA-093 (org-native).

## Rollout / migration

1. Land code + skill + tests.
2. `wt skills install` (symlink) picks up `wt-related` automatically from the repo skills dir.
3. No data migration.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — explore forks resolved in Decision)
