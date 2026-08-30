---
id: SPEC-0084
title: "Theme every recessive style in the idea views, not just the state palette"
status: rejected
owner: user
created: 2026-07-28
updated: 2026-07-28
source_idea: IDEA-103
milestone: "M4: cli ergonomics"
tags: [cli, ideas, ergonomics]
depends_on: [SPEC-0083]
---

## Rejected — why

Reverted in full. The mechanism worked at the byte level (`WT_THEME=light` turned all 81 `dim`
runs into `bright_black`, verified against the real CLI under a pty), but it produced **no visible
change on a dark terminal** — `ESC[2m` and `ESC[90m` both render as grey against a dark
background. The substitution only *looks* like anything on a light background.

The owner uses a dark terminal, so the feature was unobservable and unverifiable for the only
person running it: an env var that changes nothing you can see is not a feature. Worse, SPEC-0083
was reported as working on the strength of SGR-code counts rather than appearance, which is the
wrong evidence for a presentation change.

What survives: [SPEC-0082](./0082-color-code-idea-state-idea-incubate-specced-so.md), the state hue
palette, which is visible and unaffected by this revert.

The original risk SPEC-0082 recorded — light-background legibility — returns to being an open,
unaddressed gap. That is the honest position: it is a real limitation for a light-terminal user,
and it should not be marked closed by a change nobody can see. Anyone picking it up should note
that a partial fix (the idea views only, ~13 of ~86 `dim` sites) is not worth shipping; the whole
of `wt report` / `tasks` / `agenda` / `review` / `topics` / `digest` / the dashboard assumes dark,
so a light theme is all-or-nothing and probably wants a Rich `Theme` object rather than per-site
substitution.

## Context

[SPEC-0083](./0083-light-theme-substitution-for-dim-idea-state-styles.md) added `WT_THEME` /
`theme:` and adapted the idea *state* palette for light backgrounds. In use it appears to do
nothing, and that report is correct.

Measured: `wt ideas` in its **default view is byte-identical** under `WT_THEME=dark` and
`WT_THEME=light`. SPEC-0083 only substitutes for the four *terminal* states
(`PROMOTED`/`EXPORTED`/`DROPPED`/`RESEARCHED`), and those appear only under `--all`. Under `--all`
it does work (`2;32` → `3;32`).

But the default view **is** full of `dim` (SGR `2`) — 13 sites across the two idea views: the panel
title and filter label, the empty-state message, the table `header_style`, the `id` column, the
`updated` age column, the footer hint, and `wt next`'s drift line. Plus the headline's
done-dimming, which comes from `_state_style`.

So SPEC-0083 closed the recorded risk on the fraction of `dim` usage nobody sees daily and left the
rest alone. Its non-goal ("not re-theming the other ~86 `dim` uses") was the wrong cut: the whole
*point* of a light theme is legibility in the view you actually read, and the state palette was
merely where the risk happened to be written down. This corrects the scope.

## Goals / Non-goals

**Goals**

- Under `WT_THEME=light`, the **default** `wt ideas` and `wt next` output visibly differs from dark
  — no SGR `2` anywhere in them.
- Every recessive style in those two views resolves through one themed helper, so a future site
  cannot be missed by hand.
- Dark remains byte-identical to today.

**Non-goals**

- Not theming `wt report`, `wt tasks`, `wt agenda`, `wt review`, `wt topics`, `wt digest` or the
  dashboard. That is the remaining ~70 `dim` sites and a much larger sweep; this spec deliberately
  finishes the *idea* surfaces where the complaint arose, and the rest is tracked separately rather
  than half-done.
- No change to the hue palette from SPEC-0082/0083.
- No new config or env surface — `theme:` / `$WT_THEME` from SPEC-0083 are reused as-is.

## Decision

Add `_recessive(theme)` returning `"dim"` on dark and `"bright_black"` on light, and route every
recessive style in `ideas()` and `next_ideas()` through it — including the table's `header_style`
and the headline style for done ideas.

`bright_black` is a *named* ANSI colour, so the terminal still maps it to its own palette; unlike
`dim` it is a foreground colour rather than an intensity attribute, which is what makes it legible
against a light background.

The headline gains `_idea_headline_style(task, theme)`: recessive when the idea is done, `white`
otherwise. This replaces the two `_state_style` calls *inside the idea tables only* —
`_state_style` itself is untouched, so `wt tasks` and `wt agenda` are unaffected.

## Design

### `_recessive(theme)` (`src/wt/report.py`)

```python
def _recessive(theme: str) -> str:
    """The "quieter than the content" style for `theme` (SPEC-0084): `dim` on dark,
    `bright_black` on light, where `dim` renders close to the background."""
    return "bright_black" if theme == "light" else "dim"
```

### `_idea_headline_style(t, theme)`

```python
def _idea_headline_style(t, theme):
    """Headline style in the idea tables: recessive once the idea is done, else `white`."""
```

Scoped to the idea tables so `_state_style`'s seven other call sites keep their current behaviour.

### Call sites converted (both views)

| Site | Was | Becomes |
|---|---|---|
| panel title / filter label / counts | `[dim]` | `[{rec}]` |
| empty-state message | `[dim]` | `[{rec}]` |
| `Table(header_style="dim")` | literal | `header_style=rec` |
| `id` column | `[dim]` | `[{rec}]` |
| `updated` age column (`ideas`) | `[dim]` | `[{rec}]` |
| footer hint / drift line | `[dim]` | `[{rec}]` |
| headline when done | `_state_style` → `dim` | `_idea_headline_style` |

`theme` is resolved once per call by the existing `_theme(cfg)` — including in the early-return
paths (empty result, `--json` is unaffected), which is where a hand-conversion would most easily
miss one.

## Alternatives considered

- **Leave it as SPEC-0083 shipped** — rejected: the feature exists but is invisible in the view it
  was built for, which is worse than not having it.
- **Sweep all ~86 `dim` sites in one change** — the eventual right answer, rejected here as too
  large to verify in one step; the idea views are the reported problem and a coherent unit.
- **Substitute `italic` for `dim` as SPEC-0083 did for states** — italic suits a *semantic* marker
  ("closed"), but the id column and panel text are not closed-anything; they are simply quieter, so
  a grey foreground is the right encoding.
- **A Rich `Theme` object with named styles** — the idiomatic Rich approach and a better long-term
  shape, but it would rewrite every markup string in the module; worth doing as part of the full
  sweep, not as a bug fix.
- **Detect the background properly** — impossible; established in SPEC-0083.

## Acceptance criteria

- [x] Default `wt ideas` output under `light` differs from under `dark`.
- [x] Default `wt next` output under `light` differs from under `dark`.
- [x] Neither view emits SGR `2` (dim) under `light`, in the default view or under `--all`.
- [x] Dark output for both views is byte-identical to before this change.
- [x] The empty-result path (no matching ideas) is themed too.
- [x] `wt tasks`, `wt agenda` and `wt review` are byte-identical under both themes.
- [x] `_state_style` is unchanged and still used by the non-idea views.
- [x] `--json` output is unaffected by the theme.
- [x] SPEC-0075/0077 width and ordering invariants hold under both themes.
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_theme.py` grows to 64 tests:

- `test_default_view_differs_between_themes` — for `ideas` *and* `next_ideas`, rendered output
  differs. This is the exact regression that prompted the spec, so it is asserted first.
- `test_no_dim_under_light` — parametrised over both views × default/`--all`: no `\x1b[2m` and no
  `2;` prefix in any SGR run.
- `test_dark_output_unchanged` — golden comparison against output captured with the pre-change
  styling (constructed inline from the same rows), proving dark is untouched.
- `test_empty_view_is_themed` — no ideas at all; the "no matching ideas" line carries the themed
  style. The early-return path is the one a hand-conversion misses.
- `test_recessive_mapping` and `test_idea_headline_style` — the helpers directly, including that a
  done idea gets the recessive style and an open one does not.
- `test_other_views_unaffected` — `tasks`, `agenda` and `review` byte-identical under both themes.
- `test_json_unaffected_by_theme`.
- `test_width_invariants_under_both_themes` — widths {200, 80}, both views.

**Manual verification**

1. Rendered both views under each theme against the real corpus and counted dim (SGR `2`) runs:

   | view | default: differs? | dim in dark | dim in light |
   |---|---|---|---|
   | `wt ideas` | yes | 81 | **0** |
   | `wt ideas --all` | yes | 381 | **0** |
   | `wt next` | yes | 50 | **0** |
   | `wt next --all` | yes | 251 | **0** |

   **Done** — the default view now differs, which is precisely what SPEC-0083 failed to achieve.
2. `wt tasks` identical under both themes. **Done.**

**Regression guard**

Full `uv run pytest`, especially `tests/test_idea_state_color.py`, `tests/test_idea_table_width.py`,
`tests/test_idea_freshness.py` and `tests/test_tasks.py`.

## Clock Log

Clocked on IDEA-103 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

Presentation only. Dark is the default and is unchanged, so nothing shifts for anyone who has not
opted in.

**Remaining work, stated so it is not mistaken for done:** `wt report`, `wt tasks`, `wt agenda`,
`wt review`, `wt topics`, `wt digest` and the dashboard still assume a dark background (~70 `dim`
sites). A light-theme user will find those views hard to read. The full sweep — probably via a Rich
`Theme` object rather than per-site substitution — is the follow-up.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Why did SPEC-0083 appear to do nothing?* → it themed only the terminal-state palette, which is
  invisible without `--all`.
- *`italic` or grey for non-semantic recessive text?* → grey (`bright_black`); italic encodes a
  meaning these sites do not have.
- *Scope* → the two idea views in full; the rest of wt is a separate sweep, recorded in Rollout.
