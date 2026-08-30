---
id: SPEC-0057
title: "Relationship pointers: folded-into / superseded-by"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
parent: SPEC-0055
source_idea: IDEA-067
milestone: "M4: cli ergonomics"
depends_on: [SPEC-0056]
tags: [ideas, workflow, lifecycle]
---

## Context

Child of [SPEC-0055](./0055-complete-the-idea-terminal-outcome-model-first.md), building on
[SPEC-0056](./0056-generic-wt-idea-close-verb-researched-state-reason.md). When an idea is
closed because its value moved elsewhere (e.g. `IDEA-062`'s predicate folded into `IDEA-059`,
or a design superseded by another idea), that pointer should be durable and discoverable — not
lost in prose. SPEC-0056's `close_idea` + `set_property` are the mechanism; this spec
adds the pointer flags and surfacing.

## Decision

Extend `wt idea close` with `--folded-into SELECTOR` and `--superseded-by SELECTOR`. Each
resolves to an idea/spec id, is written as a property (`FOLDED_INTO` / `SUPERSEDED_BY`),
cross-linked as `[[<id>]]` in the close Log line, and surfaced in `wt idea show` / `--json`.

## Design

- **CLI (`cli.py`):** add `--folded-into` / `--superseded-by` to `idea close`; pass through to
  `close_idea`.
- **`close_idea` (`explore.py`):** accept `folded_into` / `superseded_by`; resolve each via
  `resolve_selector` to its canonical id (validate it exists; error cleanly otherwise); write
  `FOLDED_INTO` / `SUPERSEDED_BY` via `set_property` (SPEC-0056); include `[[<id>]]`
  cross-links in the close Log note.
- **Surfacing (`explore.py`):** `idea_show_payload` includes `folded_into` / `superseded_by`
  (from properties) when present; `format_idea_show` prints a `→ folded into [[<id>]]` /
  `→ superseded by [[<id>]]` line under the header.

## Alternatives considered

- **Pointers as a free-text Log note only** — rejected: not queryable; a property lets tools
  (and a future `wt` view) follow where value landed. Keep the Log cross-link *and* the
  property.
- **A generic `--link TYPE ID`** — over-general for now; two named flags are clearer and match
  the two real relationships.

## Acceptance criteria

- [x] `wt idea close IDEA-062 --as researched --folded-into IDEA-059` sets `:FOLDED_INTO:
      IDEA-059`, a `[[IDEA-059]]` cross-link in the Log, and (with SPEC-0056) `RESEARCHED`.
- [x] `--superseded-by SPEC-0033` (or an idea id) sets `:SUPERSEDED_BY:` with a cross-link.
- [x] An unresolvable pointer target errors with no file write.
- [x] `wt idea show` and `--json` surface the pointer(s) when present, absent otherwise.

## Test plan

- **Automated tests** (extend `tests/test_close.py`): `--folded-into`/`--superseded-by` write
  the property + Log cross-link and canonicalize the id; unresolvable target raises with no
  write; `show`/`--json` expose the pointer; closing without a pointer leaves the keys absent.
- **Manual verification:** `wt idea close IDEA-062 --as researched --folded-into IDEA-059`;
  `wt idea show IDEA-062` shows the folded-into link; `--json` includes `folded_into`.
- **Regression guard:** `uv run pytest` green; ideas without pointers unchanged in show/json.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green; manual step performed.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.
