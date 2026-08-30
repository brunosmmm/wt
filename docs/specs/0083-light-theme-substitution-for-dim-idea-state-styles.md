---
id: SPEC-0083
title: "Theme-adapt the idea state palette: substitute dim on light backgrounds"
status: rejected
owner: user
created: 2026-07-28
updated: 2026-07-28
source_idea: IDEA-103
milestone: "M4: cli ergonomics"
tags: [cli, ideas, ergonomics]
depends_on: [SPEC-0082]
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

[SPEC-0082](./0082-color-code-idea-state-idea-incubate-specced-so.md) shipped a hue palette for the
idea `state` cell and recorded one accepted risk: legibility on light-background terminals is
untested, and wt has no theme configuration. This closes that.

Measured before designing, because it determines how much is worth building:

- **Rich already handles every terminal capability wt could want.** `NO_COLOR=1` → `color_system
  None`, `no_color True`; `TERM=dumb` → colour off; non-tty → colour off; `FORCE_COLOR=1` →
  truecolor. Nothing to add.
- **Terminals do not reliably expose light-vs-dark.** `COLORFGBG` is the only env var that encodes
  it and is **unset** on this machine's `tmux-256color`; only a handful of terminals set it. The
  alternative — an OSC 11 background query — needs raw-mode tty access and a timed read, breaks
  under tmux/ssh, can hang, and risks leaking escape bytes into piped output. Unacceptable for a
  command that is frequently piped.
- **Most of the palette was never at risk.** `cyan`, `green` and `red` are *named ANSI* colours, so
  the terminal maps them to its own theme — they adapt for free. The single theme-sensitive token is
  `dim` (SGR 2), which some light themes render close to the background.

So there is no detection problem to solve, only a substitution one.

## Goals / Non-goals

**Goals**

- On a light background, the idea state palette stops relying on `dim`.
- The theme is explicit and cheap to set; `auto` uses `COLORFGBG` when the terminal provides it.
- Dark terminals — the default — render exactly as they do today.

**Non-goals**

- No OSC 11 / terminal querying, for the reasons above.
- No change to `NO_COLOR` / `FORCE_COLOR` / tty handling; Rich covers it.
- **Not** re-theming the other ~86 `dim` uses across wt (`_state_style`, panels, hints, the
  agenda). This closes SPEC-0082's recorded risk for the palette it introduced; a general
  light-theme pass is separate and much larger.
- No colour customisation beyond the light/dark switch — a full user-defined palette is not the
  gap that was recorded.

## Decision

Add a theme resolved once per render, in priority order:

1. `cfg["theme"]` — `"dark"` | `"light"` | `"auto"` (default `"auto"`)
2. `$WT_THEME` — same values, overrides config for a one-off invocation
3. under `auto`: `$COLORFGBG`, whose trailing field is the background colour index — `7`, `15` or
   a high value means light
4. otherwise `dark`

On `light`, the idea state palette replaces the `dim` token with **`italic`** (plus
`bright_black` where `dim` stood alone). Both are named/attribute styles, so they stay
terminal-mapped rather than becoming a hardcoded grey.

*(As-built correction.)* The draft said to simply *drop* `dim` on light backgrounds. Deriving the
palette and reading it back showed that is wrong: `dim green` → `green` makes `PROMOTED`
**identical to `SPECCED`**, and `dim cyan` → `cyan` makes `EXPORTED` identical to `INCUBATE`. `dim`
was carrying the open/closed axis, so removing it collapsed two axes into one. `italic` takes over
as the recessive marker, preserving *recessive = closed, hue = which path*. Caught by inspecting
the derived dict, not by rendering — a reminder that a derivation needs its output read.

## Design

### `_theme(cfg)` (`src/wt/report.py`)

```python
def _theme(cfg) -> str:
    """"dark" | "light" (SPEC-0083). cfg['theme'] / $WT_THEME / $COLORFGBG, in that order."""
```

`COLORFGBG` parsing is deliberately forgiving: the value is `fg;bg` (sometimes `fg;default;bg`), so
the *last* field is taken and a non-numeric value falls through to `dark`. An absent or unparseable
value must never raise inside a listing command.

### `_idea_state_style(t, theme=None)`

Looks up `_IDEA_STATE_STYLES` as today, then on `light` rewrites the style's `dim` token to
`bright_black`:

`_IDEA_STATE_STYLES_LIGHT` is derived from the dark palette at import time by `_light_variant`,
which maps `dim X` → `italic X` and bare `dim` → `italic bright_black`. Deriving rather than
hand-writing keeps the two from drifting; a test asserts they cover the same keys.

Concretely on light: `PROMOTED` → `italic green`, `EXPORTED` → `italic cyan`,
`DROPPED` → `italic red`, `RESEARCHED` → `italic bright_black`. Verified against the real corpus:
`SPECCED` renders `32` while `PROMOTED` renders `3;32`, so open and closed remain distinguishable.

`theme` is passed in by the callers so it is resolved once per table, not once per row.

### Config

`config.py` gains `"theme": "auto"` in `DEFAULT_CONFIG`. No migration; an absent key reads as
`auto`.

## Alternatives considered

- **OSC 11 background query** — the only way to truly detect the background. Rejected: raw-mode tty
  read, hangs under tmux/ssh, leaks escape bytes when piped.
- **Hardcode a grey (`grey50`, `#888`)** — legible on both, but abandons terminal-palette mapping,
  which is the property that makes the rest of the palette work everywhere.
- **Drop `dim` entirely and distinguish terminal states by hue alone** — simpler, but loses the
  "closed" signal that SPEC-0082 deliberately encoded.
- **A full user-defined palette in config** — more flexible and more surface than the recorded risk
  justifies.
- **Do nothing** — defensible, since dark terminals are the common case; rejected because the risk
  was explicitly recorded as a known gap rather than accepted forever.

## Acceptance criteria

- [x] `_theme({})` is `"dark"` when `COLORFGBG` and `WT_THEME` are unset.
- [x] `cfg["theme"] = "light"` yields `"light"`; `"dark"` yields `"dark"`.
- [x] `$WT_THEME` overrides `cfg["theme"]`.
- [x] Under `auto`, `COLORFGBG=0;15` and `15;0`-style values resolve light vs dark by the **last**
      field; a malformed value falls back to `dark` without raising.
- [x] On `dark`, every state's style is byte-identical to SPEC-0082's palette.
- [x] On `light`, no style contains `dim`.
- [x] On `light`, the four terminal states remain mutually distinguishable.
- [x] On `light`, no terminal state's style equals an open state's — the axis `dim` was carrying
      must survive the substitution.
- [x] On `light`, every terminal state retains a recessive marker (`italic`).
- [x] Both palettes parse as Rich styles and cover exactly the same set of states.
- [x] The light palette is *derived* from the dark one, so adding a state to one adds it to both.
- [x] `wt ideas` / `wt next` render without error under both themes; no width or ordering change.
- [x] `wt tasks` / `wt agenda` are untouched by the theme.
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_theme.py` (39 tests):

- `test_theme_defaults_to_dark`, `test_config_theme_wins`, `test_env_overrides_config`.
- `test_colorfgbg_variants` — parametrised over `"0;15"`, `"15;0"`, `"7"`, `"0;default;15"`,
  `"garbage"`, `""`: asserts the resolved theme, with malformed input falling back to dark rather
  than raising. The parser is the only part with real edge cases, so it is enumerated.
- `test_dark_palette_unchanged` — equals SPEC-0082's mapping exactly.
- `test_light_palette_has_no_dim` and `test_light_terminal_states_still_distinct`.
- `test_palettes_cover_the_same_states` — the derivation guard: the two dicts have identical keys.
- `test_both_palettes_parse`.
- `test_tables_render_under_both_themes` — `ideas()`/`next_ideas()` at a fixed width under each
  theme; all columns present, no line over the width (SPEC-0075 invariants).
- `test_light_theme_does_not_touch_tasks` — the tasks table renders identically under both.

**Manual verification**

1. `uv run wt ideas` — unchanged (dark default). **Done.**
2. `WT_THEME=light` over the real corpus, read back as SGR codes: `SPECCED` `32`,
   `PROMOTED` `3;32`, `EXPORTED` `3;36`, `DROPPED` `3;31`, `RESEARCHED` `3;90` — no `2` (dim)
   anywhere, all four terminal states distinct, and none colliding with an open state. **Done.**
3. `COLORFGBG=0;15` → `_theme` resolves `light`. **Done.**

**Regression guard**

Full `uv run pytest`, especially `tests/test_idea_state_color.py` (SPEC-0082's palette),
`tests/test_idea_table_width.py` and `tests/test_idea_freshness.py`.

## Clock Log

Clocked on IDEA-103 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

Presentation only. Default `auto` resolves to `dark` on any terminal that does not advertise a
light background, so existing behaviour is preserved unless a user opts in.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Can the theme come from the terminal?* → only via `COLORFGBG`, which most terminals do not set;
  OSC 11 is unsafe for a piped CLI. Hence config + env with `COLORFGBG` as a best-effort `auto`.
- *Why not a hardcoded grey?* → it abandons terminal-palette mapping, the property that makes the
  named colours work everywhere.
- *Scope* → the SPEC-0082 palette only; wt's other ~86 `dim` uses are a separate, larger pass.
