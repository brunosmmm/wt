---
id: SPEC-0069
title: "Dedicated post-mortem/defect annotation mechanism, bidirectional"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-082
milestone: "M4: cli ergonomics"
tags: [process, cli]
---

## Context

Promoted from idea `IDEA-082` (Dedicated post-mortem/defect annotation mechanism, bidirectional spec<->idea).

  :PROPERTIES:
  :ID: IDEA-082
  :END:
** Summary
Gap found while investigating a real bug (SPEC-0063's parse_clock_log silently dropping unbracketed timestamps against DEMO-0007, fixed in commit 2395182): wt has no dedicated mechanism for recording 'a defect was found in already-`done` work.' Today the only option is `wt idea log <ID> --note ...` — a generic dated Log entry that:

1. Lives only on the **idea's** org node, never on the **spec** file itself (the schema has no post-mortem/lessons-learned section for specs at all).
2. Requires the person/agent finding the bug to already know (or go hunt down) which idea originally owned the affected area — there is no reverse index from 'this code path' or 'this SPEC-NNNN' back to its source idea.
3. Is indistinguishable in shape from an ordinary exploration Log note — nothing marks it as a post-mortem/defect record specifically, so it cannot be filtered, listed, or surfaced separately (e.g. no `wt bugs` or `wt postmortems` view).

`wt spec fit-log` is the closest existing relative but is framed narrowly around post-ship **fit** (did it solve the problem), is outbound-only, and auto-prefixes notes with "fit-log:" — not a good fit for "we found and fixed a defect in shipped code."

Decision direction (not yet finalized): a small, generic primitive — e.g. `wt spec postmortem <SPEC-ID> --note "..."` — that (a) resolves the spec's `source_idea` the same way `fit_log` already does, (b) appends a distinctly-labeled Log entry (e.g. a `*** POSTMORTEM` headline instead of a plain dated one, mirroring SPEC-0054's OPEN/RESOLVED question-state convention) onto that idea, and (c) is listable/filterable later (`wt idea log --kind postmortem` or similar), for both internal and outbound specs — unlike `fit-log` which is outbound-only.
** Open questions
*** RESOLVED Should this work for internal specs too, or only outbound (mirroring fit-log's current scope)?
*** RESOLVED Distinct org headline marker (e.g. *** POSTMORTEM) vs. just a plain Log note with a conventional prefix — worth the extra org-parsing surface?
*** OPEN Should wt hub/wt digest surface a count of open postmortems anywhere, or is 'findable via wt idea show' enough?
** Log
*** [2026-07-26 Sun 13:58]
Checked feasibility of both open design questions against the actual codebase.

**Internal vs outbound scope (Q1):** trivially both. `specs.py::resolve_spec_path(cfg, spec_id)` already resolves **either** an internal `SPEC-NNNN` or an outbound `PROJ-NNNN` id uniformly (via `_is_outbound_spec_id`), and both internal and outbound spec frontmatter already carry `source_idea:` (confirmed: SPEC-0065..0068's own frontmatter all have it). `fit_log`'s current outbound-only limitation is just that it calls `_find_outbound_spec` directly instead of the already-existing unified `resolve_spec_path` — swapping that one call generalizes it for free, no new resolution logic needed.

**Headline convention vs plain Log note (Q2):** plain Log note wins clearly. A distinct `** POSTMORTEM` headline type (mirroring SPEC-0054's `** OPEN|RESOLVED` questions) would require real dedicated machinery: a new regex (`_QHEAD_RE`-equivalent), a `#+TODO` declaration so orgparse recognizes it as a real keyword state, and replace/append/resolve/normalize functions — a SPEC-0054-sized effort for something far rarer than open questions. A plain dated Log entry with a conventional prefix (mirroring `fit_log`'s own auto-prepended `"fit-log: "`, e.g. `"postmortem: "`) reuses 100% of the existing `append_log` machinery, filterable later with a simple grep/substring check if needed — no new org-parsing surface at all.

**wt hub/digest surfacing (Q3):** still genuinely open, not trivially resolvable like the other two. `hub_payload()` and `digest()` both work off spec **frontmatter** fields (status/kind/milestone) — neither scans idea Log **bodies** today. Surfacing a postmortem count would need a new kind of scan (grep Log sections for the prefix across every idea), which is a real, separate addition, not a reuse of an existing field. Leaving this open as a later nice-to-have rather than blocking a first version on it.

## Goals / Non-goals

**Goals**
- Add `wt spec postmortem <SPEC-ID> --note "..."`: appends a dated, distinctly-prefixed
  ("postmortem: ") Log entry onto the spec's linked source idea, for internal (`SPEC-NNNN`)
  and outbound (`PROJ-NNNN`) specs alike.
- Extract the spec-id → source-idea resolution logic currently embedded inline in `fit_log`
  into a shared helper, and generalize it to use `specs.resolve_spec_path` (handles both id
  shapes) instead of `_find_outbound_spec` (outbound-only) — as a direct, low-cost side
  effect, this also fixes `fit_log`'s existing internal-spec limitation, found trivial during
  explore.
- Reuse the existing `append_log`/Log-section machinery entirely — no new org headline type,
  no new `#+TODO` keyword, no new parsing surface (Q2's resolution).

**Non-goals**
- No `wt hub`/`wt digest` surfacing of a postmortem count (Q3 explicitly deferred during
  explore) — findable via `wt idea show <id>` or a plain grep for now; revisit if postmortems
  pile up unnoticed in practice.
- No structured `--kind postmortem` filter/list command in this pass — the `"postmortem: "`
  text prefix is the only marker. A dedicated filter view is future work if it proves needed.
- Not writing anything onto the spec markdown file itself — the annotation lives on the
  idea's Log only (same shape as `fit_log`): the idea is the durable annotation home, the spec
  file stays "what shipped," not an accumulating changelog.
- Not idempotent by design (unlike `pull-clock`) — running `postmortem` twice with different
  notes appends two entries; that's the point (each real finding is its own dated record).

## Decision

Extract `fit_log`'s resolution logic into a shared `_resolve_source_idea(cfg, spec_id)`
helper in `export.py`, generalized to call the existing unified `specs.resolve_spec_path`
(already handles internal-or-outbound) instead of `_find_outbound_spec`. Add
`postmortem(cfg, spec_id, note)` alongside `fit_log`, sharing that helper — the two differ only
in their auto-prefix text (`"postmortem: "` vs `"fit-log: "`). Wire `wt spec postmortem` in the
CLI with a completer covering both internal and outbound spec ids.

## Design

- **`export.py`, new `_resolve_source_idea(cfg, spec_id)`** (replacing the inline block
  currently duplicated in `fit_log`):
  ```python
  def _resolve_source_idea(cfg, spec_id):
      from .specs import resolve_spec_path
      from .org import filter_tasks, load_tasks
      source_path = resolve_spec_path(cfg, spec_id)
      fm, _ = split_frontmatter(source_path.read_text())
      fm = fm or {}
      selector = (fm.get("source_idea") or "").strip()
      if selector:
          return selector
      matches = [t for t in filter_tasks(load_tasks(cfg), is_idea=True)
                 if (t.properties.get("SPEC") or "").strip() == spec_id]
      if not matches:
          raise ValueError(f"no source idea linked to {spec_id!r} "
                           f"(set source_idea on the spec or :SPEC: on an idea)")
      if len(matches) > 1:
          ids = ", ".join((t.properties.get("ID") or t.id) for t in matches)
          raise ValueError(f"ambiguous ideas for {spec_id!r}: {ids}")
      return matches[0].properties.get("ID") or matches[0].id
  ```
- **`fit_log`** rewritten to call `_resolve_source_idea` instead of its current inline
  `_find_outbound_spec`-based block — behavior for outbound specs is unchanged, and internal
  specs now work too (bonus fix, covered by a regression test below).
- **New `postmortem(cfg, spec_id, note)`**, same shape as `fit_log`:
  ```python
  def postmortem(cfg, spec_id, note):
      from . import explore as EX
      note = (note or "").strip()
      if not note:
          raise ValueError("--note is required")
      if not note.lower().startswith("postmortem"):
          note = f"postmortem: {note}"
      selector = _resolve_source_idea(cfg, spec_id)
      path = EX.append_log(cfg, selector, note)
      idea = resolve_selector(cfg, selector)
      idea_id = idea.properties.get("ID") or idea.id
      return idea_id, path
  ```
- **`completion.py`, new `complete_any_spec_id`**: union of `complete_spec_id`'s and
  `complete_outbound_id`'s id lists, for the new command's argument completion.
- **`cli.py`**: `wt spec postmortem <SPEC-ID> --note "..."`, mirroring `spec_fit_log_cmd`'s
  shape but using the new completer and calling `postmortem` instead of `fit_log`.

## Alternatives considered

- **Distinct `*** POSTMORTEM` org headline/keyword** — rejected per Q2's explore finding:
  requires SPEC-0054-sized dedicated machinery (regex, `#+TODO` declaration, replace/append/
  resolve/normalize functions) disproportionate to how rarely this fires compared to open
  questions.
- **Leave `fit_log` untouched, don't generalize it** — rejected: the shared-helper refactor
  costs nothing extra (same helper either way) and fixes a real, already-identified limitation;
  leaving two near-identical commands with different scope (`fit-log` outbound-only,
  `postmortem` both) would just be confusing for no reason.
- **Write the postmortem onto the spec file's own body instead of the idea's Log** — rejected:
  no such section exists in the spec schema, and specs are meant to reflect "what shipped," not
  accumulate a changelog; the idea already serves as the durable, append-only record for this
  kind of note (matches `fit_log`'s existing precedent).

## Acceptance criteria

- [x] `wt spec postmortem <SPEC-ID> --note "..."` appends a `"postmortem: "`-prefixed dated Log
      entry onto the linked idea, for an internal (`SPEC-NNNN`) spec id.
- [x] Same command works for an outbound (`PROJ-NNNN`) spec id.
- [x] `wt spec fit-log` continues to work unchanged for outbound specs (regression) and now also
      works for an internal spec id (bonus fix from the shared resolver).
- [x] A spec id with no resolvable source idea (neither `source_idea` frontmatter nor a
      matching `:SPEC:` idea) raises a clear error from both `postmortem` and `fit-log`.
- [x] The appended entry is a plain dated Log headline — no new org keyword state, no `#+TODO`
      change.

## Test plan

- **Automated tests:** `tests/test_fit_log.py` (shipped location — this area's existing test
  file, not `test_export.py` as originally sketched) — `postmortem()` on an internal spec
  appends a correctly-prefixed Log entry onto the linked idea; same for an outbound spec; a
  spec id with no resolvable source idea raises; `fit_log` regression test confirms unchanged
  outbound behavior plus a **new** case proving it now also works on an internal spec id; CLI
  wiring test for `wt spec postmortem`.
- **Manual verification:** run `wt spec postmortem SPEC-0063 --note "..."` for real, confirming
  it lands correctly on `IDEA-075` alongside the existing raw `wt idea log` stopgap entry
  already there from before this command existed.
- **Regression guard:** full `uv run pytest` green; existing `fit-log` CLI/behavior unchanged
  for all currently-outbound use.

## Rollout / migration

1. Add `_resolve_source_idea`, refactor `fit_log` to use it, add `postmortem` — one
   self-contained change, no data migration, no dependency on other specs.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- None blocking. `wt hub`/`wt digest` surfacing (Q3) is intentionally deferred — see
  Non-goals.
