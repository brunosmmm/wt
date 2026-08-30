---
id: SPEC-0054
title: "Custom org TODO keywords for Open-questions items (OPEN/RESOLVED)"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
source_idea: IDEA-063
tags: [ideas, org, explore]
---

## Context

Promoted from `IDEA-063`. Under an idea's `** Open questions` section, an item's
open-vs-closed state is today encoded in at least five mutually inconsistent, ad-hoc ways
across `ideas.org`:

- `+ [ ]` / `+ [X]` org checkboxes,
- plain `-` bullets (open only by convention),
- a `_Resolved:_` prose sub-header grouping,
- an inline `(resolved)` / `(open)` prefix per bullet,
- empty section or free prose.

None of these is a machine-readable open/closed signal, so neither a human skimming nor
`wt idea show` / `--json` can tell reliably which questions are still open. (This very
spec's source idea reproduced the anti-pattern — proof the convention does not hold itself.)

Research (root = this wt checkout) established the shape and the one real hazard:

- The enrichment read/write layer (`src/wt/explore.py`) is a **hand-rolled line parser**
  (`_find_sections` slices the body between the level-≥2 `Summary` / `Open questions` / `Log`
  headers). It is independent of orgparse, so nesting level-3 question headlines inside the
  section still slices cleanly.
- But `src/wt/org.py:load_tasks` parses the same files with orgparse and turns **every** node
  into a `Task`. Verified with orgparse that a file may carry two `#+TODO:` lines whose
  keywords pool; `OPEN`/`RESOLVED` then parse as real todo states (`RESOLVED` a done-key) and,
  being outside `org_idea_keywords`, never register as ideas. However `report.tasks`' default
  view keeps any node with `state is not None`, `is_done` false, `is_idea` false — so an
  `*** OPEN <question>` node **would leak into `wt tasks`** as a spurious actionable task.
  Today's `*** [timestamp]` Log nodes stay out only because they are *stateless*; giving
  questions real state breaks that incidental safety.

## Goals / Non-goals

**Goals**
- Give each open question a single, machine-readable state via a question-scoped org TODO
  sequence `OPEN | RESOLVED`.
- Keep every enrichment node (Summary/Log/questions body) out of `wt tasks`/`wt agenda`.
- Let agents/humans set and flip question state through `wt idea questions`.
- Deterministically migrate the existing ad-hoc forms already in `ideas.org` — no LLM rewrite,
  no dropped text.

**Non-goals**
- Changing the idea-state vocabulary (`IDEA/INCUBATE/…`) or the Summary/Log sections.
- Any new idea state; questions live under the existing `INCUBATE`/`IDEA` idea.
- Rich per-question due dates, priorities, or threading.

## Decision

Model each open question as a **level-3 org headline** under `** Open questions`, stated with a
question-scoped TODO sequence: `*** OPEN <text>` / `*** RESOLVED <text>`. Declare the sequence
as a **second** `#+TODO: OPEN | RESOLVED` header line in `ideas.org` (alongside the existing
idea-state `#+TODO:` line); orgparse pools the two and neither collides.

To prevent leakage (the researched hazard), adopt the **blanket rule**: *a node nested under an
idea-state headline is enrichment and is never a task.* `load_tasks` excludes such descendants
from the task model, so Summary/Log/question nodes all stay out of `wt tasks`/`wt agenda`
regardless of their state.

`wt idea questions` gains `--state open|resolved` (on add) and a deterministic
`--resolve <n>` to flip an existing question; `wt idea show` renders resolved questions
distinctly and `--json` exposes structured `{state, priority, text}` items. A new
`wt idea normalize-questions` command backfills the legacy forms (mirroring the existing
`wt idea normalize-logs`, SPEC-0031).

**Reality check (what the real `ideas.org` contained).** The historical forms turned out to
be richer than the initial "≥5": questions were also used as *decision logs* with leading
status **labels** — `RESOLVED — …`, `RESOLVED (round 1): …`, `OPEN (…): …`, `LOCKED: …`,
`OPTIONAL: …`, `Remaining: …`, plus `_Resolved in explore (date):_` group headers and
standalone `_None blocking…_` notes. The naive classifier prepended `OPEN`, producing garbage
like `*** OPEN RESOLVED …` / `*** OPEN LOCKED …`. Two decisions followed (see
*Alternatives*): (1) map leading labels to state — `RESOLVED`/`LOCKED` → RESOLVED,
`OPEN`/`OPTIONAL`/`Remaining` → OPEN — stripping the label word; `OPTIONAL` also gets an org
priority cookie `[#C]` so "optional" survives as structured priority, not prose. (2) The
migration is **verbatim** — it never runs the SPEC-0030 Markdown→org pass, so existing text
(backticks, `**` inside `=…=`) is preserved byte-for-byte. Fresh `--set`/`--add` input still
normalizes markdown, matching prior `set_questions` behavior.

## Design

**Keyword config.** Add `org_question_keywords` to `config.py` defaults:
`["OPEN", "|", "RESOLVED"]` (same `|`-split convention as `org_idea_keywords`). `org.py`
exposes `question_keywords(cfg)` → `(opens, dones)` via `_split_keywords`.

**File header.** On any question write (and in `normalize-questions`), ensure `ideas.org`
declares `#+TODO: OPEN | RESOLVED`. A helper in `explore.py`/`org_write.py` inserts the line
after the existing `#+TODO:` header if absent (idempotent). Required because a file's own
`#+TODO` wins over the env fallback, so orgparse only recognizes `OPEN`/`RESOLVED` once the
line is present.

**Enrichment exclusion (leakage fix).** In `org.py`:
- `_node_to_task` / `load_tasks`: compute `is_enrichment` by walking a node's orgparse
  ancestors; true if any ancestor's `todo` is in `idea_keywords`. Idea headlines themselves
  are *not* enrichment (no idea ancestor).
- `load_tasks` skips `is_enrichment` nodes entirely (they are neither tasks nor ideas). This
  supersedes the incidental "stateless Log nodes don't show" behavior with an explicit rule
  and also future-proofs any later stateful enrichment.

**Question model + read/write (`explore.py`).** An item is `{state, priority, text}`
(`priority` is an org cookie letter `A|B|C` or `None`); the on-disk form is
`*** OPEN|RESOLVED [#P] text`.
- `_classify_question_lines(text) -> list[item]`: the single deterministic parser used by both
  read and migration. Recognizes, in order: normalized `*** OPEN|RESOLVED [#P]` headlines;
  `_Resolved…_` group headers (sets a sticky RESOLVED state for following bullets); `[X]`/`[ ]`
  checkboxes; `(resolved)`/`(open)` prefixes; leading status **labels** (`_QLABEL_MAP`:
  RESOLVED/LOCKED→resolved, OPEN/OPTIONAL/Remaining→open, OPTIONAL carrying `[#C]`), stripping
  the label + separator; bare bullets (→ group state or OPEN); indented continuation lines
  (appended to the previous item). Nothing is ever dropped.
- `read_idea_questions(cfg, task)`: `_classify_question_lines` over the sliced body.
- `_items_to_question_body(items, normalize_text=True)`: render headlines with the priority
  cookie. Markdown→org is applied to **each item's text only, never the assembled line** — the
  leading `***` would otherwise pair with `**` inside the text and eat both stars
  (`=** Summary=` → `=* Summary=`). Migration passes `normalize_text=False` (verbatim).
- `set_questions(text)`: classify → headlines (fresh input, markup normalized).
- `add_question(bullet, state="open")`: append one headline; existing lines untouched.
- `resolve_question(index)`: 1-based over classified items; flip to RESOLVED, text unchanged;
  out-of-range → `ValueError`, no write.
- `_replace_section_body(..., apply_markup=False)` is the write path for pre-rendered question
  bodies so the outer `to_org_body` never re-mangles them.

**CLI (`cli.py` `idea questions`).** `--state [open|resolved]` (with `--add`, default `open`),
`--resolve N`; exactly one of `--set`/`--add`/`--resolve`. New `normalize-questions` command
mirrors `normalize-logs`.

**Show / JSON.** `format_idea_show` renders `*** OPEN|RESOLVED [#P] text` (state visible in the
keyword). `idea_show_payload` / `--json` (`wt.idea.v1`) adds a
`question_items: [{state, priority, text}]` array; the raw `questions` string stays for
back-compat.

**Migration — `wt idea normalize-questions`.** Per-idea (or whole ideas file), re-resolving by
`:ID:` between writes (each write shifts line numbers). Rebuilds each Questions body via
`_classify_question_lines` + `_items_to_question_body(normalize_text=False)`; writes only when
the body changes (idempotent), and ensures the `#+TODO: OPEN | RESOLVED` header once.

## Alternatives considered

- **Question-keyword exclusion set (narrow leakage fix)** — only drop nodes whose state is in
  `org_question_keywords`. Rejected: the blanket idea-descendant rule is simpler, covers Log
  and Summary too, and future-proofs later enrichment kinds.
- **Normalized bullet cookie (`- [OPEN] …`) instead of headlines** — avoids orgparse ever
  seeing the nodes, so no leakage. Rejected: it invents yet another bespoke syntax and forgoes
  native org state/agenda tooling; the point is to use org's own mechanism.
- **New-writes-only, no backfill** (SPEC-0032 precedent) — rejected here because the existing
  `ideas.org` is small, enumerable, and the whole value is a *consistent* file; a deterministic
  backfill is low-risk since it is code, not an LLM.
- **Leaving `OPTIONAL`/`Remaining` as prose or a tag** — rejected in favor of an org priority
  cookie (`OPTIONAL` → `[#C]`), which is structured and queryable rather than a bespoke marker.
- **Normalizing markdown during migration** — rejected: converting `` `x` `` → `~x~` or
  touching `**` inside `=…=` alters existing authxxed content; migration must be verbatim.

## Acceptance criteria

- [x] `ideas.org` carries a `#+TODO: OPEN | RESOLVED` header line after any question write.
- [x] A question written via `wt idea questions --add "…" --state open|resolved` appears as a
      `*** OPEN|RESOLVED …` headline under `** Open questions`.
- [x] `wt idea questions <ID> --resolve N` flips the Nth question to `RESOLVED` and leaves its
      text unchanged; out-of-range index errors with no file write.
- [x] No question node (`*** OPEN …` or `*** RESOLVED …`) appears in `wt tasks` (default or
      `--all`) or `wt agenda`; existing Log stamp nodes also remain absent. (Verified on the
      real `ideas.org`: 0 nodes with state OPEN/RESOLVED in `load_tasks`.)
- [x] `wt idea show` visibly distinguishes OPEN from RESOLVED; `wt idea show --json` includes a
      `question_items` array of `{state, priority, text}`.
- [x] `wt idea normalize-questions` rewrites the legacy forms — checkboxes, `(resolved)`,
      `_Resolved…_` groups, bare bullets, **and** leading status labels
      (RESOLVED/LOCKED/OPEN/OPTIONAL/Remaining) — to headlines with no text loss (verbatim),
      never doubling keywords, `OPTIONAL` → `[#C]`, and is idempotent on a second run.
- [x] Ideas still parse as ideas (`wt ideas` shows 21); no idea headline is misclassified.

## Test plan

- **Automated tests** (`tests/test_questions_state.py`, 11 tests — all passing):
  - `_classify_question_lines` over all legacy forms **and** the leading status labels
    (`test_classify_covers_all_legacy_forms`, `test_classify_leading_status_labels`).
  - `add_question` / `--state` emit headlines + ensure header; `read_idea_questions`
    round-trips `{state, priority, text}`; classifier idempotent on headlines.
  - `resolve_question(n)` flips state only; out-of-range raises with file untouched.
  - `normalize-questions` lossless + idempotent; and `test_migration_preserves_text_verbatim`
    guards against `to_org_body` mangling (`=** Summary=` and backticks preserved).
  - Header helper idempotent.
  - Leakage guard: idea with `*** OPEN`/`*** RESOLVED` questions + a Log stamp yields **zero**
    task rows (default and `--all`) while the idea still lists in `wt ideas`.
- **Manual verification (performed):** dry-ran `normalize-questions` on a scratch copy of the
  real `ideas.org` — 43 ideas rewritten, 0/160 question lines lost, no doubled/two-star
  keywords, `OPTIONAL`→`[#C]`, `_None…` kept, backticks/`**` verbatim — then applied to the
  real file (149 question headlines); `wt idea show IDEA-063`, `wt tasks --all`, `wt ideas`
  all correct.
- **Regression guard:** full `uv run pytest` green (357); `wt ideas`/`wt tasks`/`wt agenda`
  unchanged for ideas without `*** OPEN/RESOLVED` questions.

## Rollout / migration

1. [x] Land config + `org.py` enrichment-exclusion + `explore.py`/CLI changes with tests.
2. [x] Ran `wt idea normalize-questions` against the real `ideas.org` (atomic backup write);
   verified losslessness via a scratch dry-run + diff before applying.
3. [x] `python3 tools/spec_lint.py --write-ledger`; `uv run pytest`.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` — 357); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).
