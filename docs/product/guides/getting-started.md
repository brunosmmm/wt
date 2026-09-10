# Getting started

Install wt from **this** checkout (or a clone of it). PyPI’s package named `wt` is a
different tool — if `wt --help` talks about static sites (`init` / `build`), you have
the wrong binary.

## Install

```bash
uv sync                       # .venv + base deps
uv run wt --help              # verify: idea, report, projects, …
uv tool install .             # put wt on PATH
# optional desk UI:
uv tool install '.[tui]'      # from this checkout — not `uv tool install 'wt[tui]'`
```

Config and data live under XDG (`~/.config/wt/`, `~/.local/share/wt/`), not in the repo.

Optional completion:

```bash
wt completion install --shell fish   # or bash / zsh
```

## Pick a first path

### Path A — see your hours

```bash
wt                            # today + this week
wt report --week
wt topics --unmapped
wt map <base-topic> bucket=Acme
```

![Dashboard](../assets/captures/cli-wt-dashboard.svg)

![Weekly report](../assets/captures/cli-report-week.svg)

Deeper loop: [Track time](track-time.md) and [Weekly ops](weekly-ops.md).

### Path B — capture and triage ideas

```bash
wt idea "short thought"
wt ideas
wt next
```

![ideas](../assets/captures/cli-ideas.svg)

![next](../assets/captures/cli-next.svg)

How the file looks: [Org-mode storage](org-storage.md). Full pipeline: [Idea → ship](idea-to-ship.md).

### Path C — agent / automation

```bash
wt skills install
wt ideas --json
wt hub --json
wt next --json
```

![hub JSON](../assets/captures/cli-hub.svg)

Install skills, then use `/wt-orient` (or the skill that matches your step) in Cursor/Claude.
Full agent catalog (schemas + recipes): [Agent surface](agent-surface.md).
Humans can stay on the CLI or open `wt tui` ([Desk](../capabilities/tui.md)).

## Day one habit

Once install works, prefer the operating guides over one-off commands:

- [Daily ops](daily-ops.md) — agenda → tasks → next/hub → light report
- [Weekly ops](weekly-ops.md) — map unknowns → review → snapshot → close loops

Architecture overview: [Workflow architecture](../concepts/workflows.md).
