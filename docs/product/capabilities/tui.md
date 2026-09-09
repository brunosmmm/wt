# Desk (TUI)

Optional Textual **ideas desk** for humans. Agents stay on CLI + `--json`.

## Install

```bash
uv sync --extra tui                 # checkout
uv tool install '.[tui]'            # PATH entry from this checkout
wt tui
```

Without the extra, `wt tui` prints an install hint and exits 1.

## What it does

Browse / filter / search ideas, capture, edit metadata (project, state, tags), toggle
clock (`i`), open detail. Project chooser uses known projects from config + payload
(empty chooser notifies instead of hanging).

See `wt tui --help` for keys and flags. Triage without a TTY: [Hub](hub.md) /
[Ideas & next](ideas.md).
