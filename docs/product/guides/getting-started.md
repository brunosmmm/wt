# Getting started

Install wt from **this** checkout (or a clone of it). PyPI’s package named `wt` is a
different tool — if `wt --help` talks about static sites (`init` / `build`), you have
the wrong binary.

## Install

From the repo root:

```bash
uv sync                       # .venv + base deps
uv run wt --help              # verify: idea, report, projects, …
```

Put `wt` on your PATH:

```bash
uv tool install .             # base CLI
# optional desk UI:
uv tool install '.[tui]'      # from this checkout — not `uv tool install 'wt[tui]'`
```

Config and data live under XDG (`~/.config/wt/`, `~/.local/share/wt/`), not in the repo.

## Shell completion (optional)

```bash
wt completion install --shell fish   # or bash / zsh
```

## First five minutes — time

```bash
wt                            # today + this week
wt topics --unmapped          # bases with no facets yet
wt report --week              # hours by topic
```

Map a topic when you recognize it:

```bash
wt map <topic> project=MyProject
```

See [Track time](track-time.md) for the weekly loop and snapshots.

## First five minutes — ideas

```bash
wt idea "short thought" --project Meta-Tools
wt ideas
wt next
```

Agents: `wt skills install`, then `/wt-orient` in Cursor/Claude. Humans can stay on the
CLI or open `wt tui` (needs the `tui` extra).

Next: [Track time](track-time.md) or [Idea → ship](idea-to-ship.md).
