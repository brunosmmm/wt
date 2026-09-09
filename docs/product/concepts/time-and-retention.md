# Time model & retention

Operational detail for passive tracking (moved out of the root README).

## Sources

| Source | Location | Notes |
|--------|----------|--------|
| Claude Code | `~/.claude/projects/` | JSON timestamps + CWD per event |
| Cursor Agent | `~/.cursor/projects/` | `<timestamp>` in user messages; topic from folder name |
| Outlook | via `wt refresh-meetings` → `meetings.jsonl` | Attended/busy filter |

Set `cursor_transcripts_root: null` in `config.yaml` to disable Cursor ingestion.

## What hours mean

- **Passive, not clocked** for transcript/meeting signal. Org `clock-in` is supplemental
  — see [Clock](../capabilities/clock.md).
- Engagement wall-clock per topic (generation + your turn fused).
- Concurrent sessions get full credit each; billed topic hours can exceed real
  wall-clock. Reports also show de-duplicated wall-clock and a parallelism ratio.
- Topic ≈ repository, refined by JIRA key on the branch when present; remap with
  `wt map` / `wt override`.

## Gap model

Per transcript session, events are walked in time order. Each event is credited the gap
**until the next event**, capped at `gap_minutes` (default 15). Lone/trailing events get
`min_block_seconds` (default 60).

Classification rules live only in YAML (`mappings.yaml`, `overrides.yaml`); re-running
over old transcripts does not clobber them.

## Retention (critical)

Claude Code deletes transcripts older than `cleanupPeriodDays` (often **30 days**).
Without defenses, history is a rolling window.

1. Raise retention in `~/.claude/settings.json` (e.g. `"cleanupPeriodDays": 365`) if disk
   allows.
2. Run `wt snapshot` regularly — archives closed days to `history.jsonl`. Reports merge
   archive + live (live wins for days still on disk). Mappings reapply to archived days;
   time-scoped overrides do **not**.

```bash
wt snapshot
wt refresh-meetings --week
```

## Meetings

`wt refresh-meetings` uses headless Claude + an M365 MCP connector (calendar MCP). Only
attended/busy meetings count by default. OAuth expiry is the main fragility for cron.
See `wt refresh-meetings --help` and [Meetings](../capabilities/meetings.md).

## XDG layout

| Kind | Default | Env |
|------|---------|-----|
| Config / rules | `~/.config/wt/` | `WT_CONFIG_DIR` |
| Data | `~/.local/share/wt/` | `WT_DATA_DIR` |
| Cache | `~/.cache/wt/` | `WT_CACHE_DIR` |

Typical files: `config.yaml`, `mappings.yaml`, `overrides.yaml`, `meetings.jsonl`,
`history.jsonl`, `reports/`, `exports/`.

## Config sketch

```yaml
transcripts_root: ~/.claude/projects
cursor_transcripts_root: ~/.cursor/projects
work_root: ~/work
timezone: America/New_York
default_axis: topic
gap_minutes: 15
min_block_seconds: 60
```

Workflow: [Track time](../guides/track-time.md).
