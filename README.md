# wt — passive work-time tracker

`wt` reconstructs **how many hours you spent on each topic** — per day and per week —
from data you already generate, with no clocking and no in-the-moment discipline. Its
main signal is your **Claude Code session transcripts**; meetings come from **Outlook
(M365)**. It's an installable Python package (`wt`) plus a few human-editable YAML files
kept in your XDG config dir. No database.

> ⚠️ **Read [Data retention & durability](#data-retention--durability) before relying on
> this for long-term history.** Claude Code deletes old transcripts, so history is
> ephemeral unless you snapshot it.

---

## Philosophy / what it measures

- **Passive, not clocked.** Every transcript event has a timestamp; `wt` infers active
  work blocks from them. You never start/stop a timer.
- **Engagement wall-clock per topic**, *fused* (Claude's generation time + your
  reading/typing are counted together — not separated). See
  [How time is calculated](#how-time-is-calculated).
- **Full credit per concurrent stream.** If you run 3–4 Claude sessions at once, each
  topic is billed its own hours, so a day's *billed* total can exceed real wall-clock.
  That's intentional. The report also shows a `wall-clock` (de-duplicated) figure and a
  `parallelism` ratio as a sanity reference.
- **Topic = repository**, refined to a JIRA key when the branch has one, with manual
  remapping for the rest. (~89% of real time lives on non-keyed branches, so repo is the
  primary key, not the JIRA ticket.)

---

## Sources

`wt` ingests from two transcript sources automatically:

| Source | Location | Timestamp | CWD/topic |
|---|---|---|---|
| **Claude Code** | `~/.claude/projects/` | JSON field per event | JSON field per event |
| **Cursor Agent** | `~/.cursor/projects/` | `<timestamp>` tag in user messages | Derived from project folder name |

Both sources feed the same gap model, topic-resolution, mapping, and override pipeline. Set `cursor_transcripts_root: null` in `config.yaml` to disable Cursor ingestion.

---

## Quick start

`wt` is a [uv](https://docs.astral.sh/uv/)-managed package (`src/` layout, hatchling
backend). From the repo root:

```bash
uv sync                       # create .venv + install wt and deps (click, rich, pyyaml)
uv run wt                     # dashboard: today + this week
uv run wt --help              # all commands;  uv run wt <cmd> --help for each
uv run pytest                 # run the test suite
```

For a `wt` command on your PATH (no `uv run` prefix), install it as a tool:

```bash
uv tool install .             # or: pipx install .
wt                            # then just `wt …`
```

Config and data live in your XDG dirs, not the repo — see
[Files & locations](#files--locations).

**Idea → explore → spec → tasks → ship:** see [`docs/WORKFLOW.md`](docs/WORKFLOW.md).
Agent playbooks: `wt skills install`, then `/wt-orient` / `/wt-capture` / `/wt-seed` /
`/wt-explore` / `/wt-new-work` / `/wt-generate` / `/wt-export` / `/wt-implement-spec`
(post-export, in the target repo).

Typical first run:

```bash
wt topics --unmapped                       # work topics that have no facets yet
wt map thjalfi project=Thjalfi area=perf   # attach facets to a base topic
wt report --week                           # this week, by topic
wt report --week --by project              # …or grouped by the 'project' facet
```

---

## Commands

| Command | Purpose |
|---|---|
| `wt` | Dashboard: today + this-week tables. Add `--split` for the diagnostic. |
| `wt report [DATE] [-w] [--by AXIS] [--last N] [--md] [--split]` | Per-topic hours; `--by` groups by a facet. |
| `wt review [DATE] [-w] [--fix]` | Segment timeline, unclassified inbox, orphaned overrides. `--fix` maps interactively. |
| `wt export [DATE] [-w] [--last N] [--format csv\|json] [-o FILE]` | Save a tidy dataset (date, topic, hours, facet columns) to a file. |
| `wt topics [--last N] [--unmapped]` | All base topics + hours + their facets. |
| `wt tasks [--state S] [--tag T] [--project P] [--priority A] [--key] [--all]` | List org tasks (open, actionable by default); filters compose. |
| `wt agenda [DATE] [-w] [--last N]` | Tasks by `SCHEDULED`/`DEADLINE` over a date scope, plus overdue. |
| `wt digest [DATE] [-w] [--last N] [--by project]` | Tracked hours joined to org tasks by JIRA key; untracked + no-time buckets. |
| `wt add TEXT... [--state S] [--tag T]* [--priority A] [--scheduled D] [--deadline D] [--file F]` | Capture a new task (append a headline to the capture file). |
| `wt state SELECTOR STATE [--no-closed]` | Set a task's TODO state (SELECTOR = `:ID:`/`file:line`/JIRA key/heading substring). |
| `wt done SELECTOR [--no-closed]` | Mark a task done (its file's first done keyword). |
| `wt map RAW axis=value [axis=value ...]` | Assign facets to a base topic (bare value = `bucket=`). |
| `wt override SESSION START END TOPIC [--note ...]` | One-off time-scoped reclassification. |
| `wt snapshot [--through DATE]` | **Archive past days so they survive transcript cleanup.** |
| `wt refresh-meetings [DATE] [-w] [--days N]` | Pull Outlook meetings into `meetings.jsonl`. |
| `wt ingest-meetings RAWFILE` | Filter a raw calendar JSON dump (used internally). |
| `wt idea TEXT...` | **Capture only** — append an idea. List with `wt ideas`; next steps with `wt next`. |
| `wt ideas [--state S] [--all] [--reindex]` | List ideas (includes a `next` command column). |
| `wt next [--all]` | Next-step hints for open ideas (see [`docs/WORKFLOW.md`](docs/WORKFLOW.md)). |
| `wt completion bash\|zsh\|fish` | Print a shell completion script to stdout. |
| `wt completion install --shell S [--dest PATH] [--force]` | Install completion to the shell's conventional path. |

**Date selection** (on `report`, `review`, `agenda`, `digest`, `refresh-meetings`): an
optional positional `DATE` (`YYYY-MM-DD`) plus a `-w/--week` flag.

```
wt report                 today
wt report --week          this week
wt report 2026-06-01      that day
wt report -w 2026-06-01   the week containing that date
wt report --last 7        last 7 days
```

### Shell completion

`wt` ships Click 8 completion for **fish**, **bash**, and **zsh** (commands, flags, and
dynamic values like projects / SPEC ids / idea selectors).

```bash
wt completion install --shell fish          # → ~/.config/fish/completions/wt.fish
wt completion install --shell bash          # → ~/.local/share/bash-completion/completions/wt
wt completion install --shell zsh           # → ~/.local/share/zsh/site-functions/_wt
wt completion fish                          # print script only (redirect yourself)
```

Fallback (no install command): `_WT_COMPLETE=fish_source wt` (or `bash_source` /
`zsh_source`). Bash/zsh may need the install directory on the shell’s completion search
path / `fpath`.

**When you add CLI surface (SPEC-0039):**
- New **subcommands** appear on TAB automatically (the fish/bash/zsh script calls live `wt`).
  Re-run `wt completion install` only if the installed entrypoint is stale.
- New **closed-set parameters** (idea/task selectors, SPEC/outbound ids, schemes, projects,
  states, axes, …) must set `shell_complete=C.complete_…` in `cli.py`. Free-text args do not.
- `REQUIRED_SHELL_COMPLETE_NAMES` in `src/wt/completion.py` + `tests/test_completion.py`
  enforce that required param names stay wired.

---

## How time is calculated

For each session (one transcript file) `wt` walks events in time order and credits each
event the gap **until the next event**, capped at `gap_minutes` (default 15):

```
contrib = (time to next event)   if that gap <= 15 min     # still working
        = 60s                    if that gap  > 15 min     # block ended; this was the tail
```

These are summed per topic per **day** (day boundaries in your configured timezone,
default `America/New_York`). A gap longer than 15 minutes (lunch, a meeting, end of day)
**ends the block and is not counted**.

Each report line shows:

- **billed** — sum of per-topic hours (can exceed real time under parallelism).
- **wall-clock** — union of all active intervals that day (overlap de-duplicated).
- **parallelism** — billed ÷ wall-clock (≈ how many topics ran at once on average).

### What the number is — and isn't

It is **elapsed clock time a topic was actively in flight**, mixing *Claude generating /
running tools* **and** *you reading and typing*. It is **not** Claude billing time, and
**not** a clean measure of your keystrokes. Under parallel work that conflation is the
point: while Claude churns on topic A you're working topic B, and both get credit.

### `--split` diagnostic (sanity only)

`wt report --split` adds a per-day/total breakdown of **Claude-generating** vs
**your-turn** time (gap ending at an assistant/tool event vs at one of your typed
prompts; tool results are correctly treated as mid-Claude-turn). It is **transcript-only**
(excludes meetings) and is **not** "your working hours" — during Claude-gen on one topic
you're often working another. Treat it as a gut check (e.g. ~64% Claude / ~36% you).

> **Cursor caveat:** Cursor agent transcripts don't store per-event timestamps for
> assistant turns — only user messages are emitted as events. All Cursor time therefore
> appears in the "your-turn" bucket of `--split`, slightly skewing the ratio. The billed
> hours themselves are unaffected.

---

## Exporting the dataset

`wt export` writes a **tidy file** (CSV or JSON) instead of a terminal report — one row
per `(date, base topic)` with `hours`, every facet axis as its own column, and a `src`
column (`live`/`archive`). Pivot it however you like in a spreadsheet without needing
`--by`. `wt report --md` also writes a human-readable markdown report to `reports/`.

```bash
wt export                       # all available days  -> exports/all.csv
wt export --week --format json  # this week           -> exports/week_<mon>.json
wt export --last 30 -o ~/may.csv
```

CSV columns: `date, topic, hours, <facet axes…>, src`.

## Topics, mappings & overrides (the rules layer)

Resolution order, applied **per event**:

1. **Time-scoped override** (`overrides.yaml`: session + time range → topic).
2. **JIRA key** from the git branch (e.g. `user/DEMO-817-…` → `DEMO-817`).
3. **Git repo** name (`git rev-parse --show-toplevel` on the session's `cwd`).
4. **`repo:branch`** for non-trunk branches without a key.
5. **Loose-folder label** (collapsed to the top folder under `~/work`) if `cwd` isn't a
   git repo — flagged *unclassified* until you map it. `git init` a folder to track it apart.

The result is the **base topic** — the canonical key that's reported, archived, and that
mappings attach to.

### Facets (multiple organizational buckets)

`mappings.yaml` attaches **facets** to a base topic — values along independent axes:

```yaml
thjalfi:
  project: Thjalfi
  area:    drone-perf
  billable: yes
DEMO-817:
  project: Demo
  area:    logging
```

Then slice the same hours by any axis — **each view sums to the same total** (no
double-counting); a topic with no value for that axis just appears under its own name:

```bash
wt report --week --by project    # Thjalfi 8h, Demo 5h, …
wt report --week --by area       # drone-perf 8h, logging 5h, …
wt report --week                 # by base topic (default)
```

Set `default_axis` in `config.yaml` to make a facet the default grouping.

- `wt topics --unmapped` lists base topics with no facets yet.
- `wt map thjalfi project=Thjalfi area=drone-perf` assigns facets (applies retroactively, forever).
- `wt map scratch R&D` is shorthand for `bucket=R&D`.
- `wt review --fix` walks the unclassified inbox and sets the `bucket` facet as you answer.
- `wt override <session> <start> <end> <TICKET>` reclassifies a specific stretch.

### Idempotency (why re-running is safe)

`wt` recomputes everything from immutable sources each run; **all human classification
lives only in the YAML rules layer**, which the parser never writes. So re-running over
old transcripts can't clobber your work. Overrides anchor to the immutable session id +
time range, and classification is per-event, so changing `gap_minutes` never orphans an
override. (Orphaned overrides — session not found — are surfaced by `wt review`.)

---

## Meetings (Outlook / M365)

Meetings are pulled from your Outlook calendar and dropped into a single **`MEETINGS`**
bucket (no per-meeting classification). Only **attended** meetings count — the filter
keeps `isAllDay=false`, `isCancelled=false`, `responseStatus=accepted`, `showAs=busy`,
plus any subjects in `meeting_filter.allowlist`. (This matters a lot: busy-only ≈ a few
hours/week, whereas counting *tentative* recurring invites balloons to ~30 h/week of
noise.)

### Connector setup (important, and fiddly)

- Calendar access is an **calendar connector** extension. OAuth alone is **not** enough — you
  must install/connect Microsoft 365 at **https://example.com/mcp** once, or calendar
  calls fail with *"Microsoft 365 isn't connected…"*.
- There are **two** MCP connectors that both front the same calendar MCP backend: the
  claude.ai-managed **`M365 connector`** and a separate **`m365`** server. They're mutually
  exclusive per session. `wt refresh-meetings` uses whichever exposes
  `mcp__m365__search_events` and is configured at **user scope** (so it's available to
  headless runs from any directory).

### How the refresh works

`wt refresh-meetings` shells out to **headless Claude** (`claude -p`) to call the MCP,
because MCP tools are only callable from inside a Claude session — a plain script can't
reach them. To stay deterministic it harvests the **raw tool result from
`--output-format stream-json`** rather than asking the model to write the file (the model
truncates large JSON). The m365 tools are *deferred*, so the headless prompt also allows
`ToolSearch`. `wt` then filters the raw dump and upserts `meetings.jsonl` (dedup by
event id).

- **OAuth token expiry is the main fragility** for unattended runs: when the token
  lapses you must re-auth interactively via `/mcp`. The refresh warns (and leaves
  `meetings.jsonl` unchanged) if it harvests nothing.
- *Known caveat:* refreshing the current/future week pulls scheduled-but-not-yet-attended
  meetings (an accepted+busy meeting tomorrow will count).

---

## Data retention & durability

**This is the most important operational fact about `wt`.**

`wt` recomputes from your Claude Code transcripts in `~/.claude/projects/`. **Claude Code
deletes transcripts older than `cleanupPeriodDays`** (default **30 days**). So by default
your history silently shrinks to a ~30-day rolling window — useless for monthly trends.

Two defenses, both recommended (and both already applied in this setup):

1. **Raised retention.** `~/.claude/settings.json` sets `"cleanupPeriodDays": 365`, so
   raw transcripts are kept ~a year. Costs disk (~1 GB/yr) but keeps full-fidelity data.
2. **`wt snapshot` — the durable archive.** Writes each **closed** (past) day's per-topic
   totals to `history.jsonl`. Reports then read **archive + live transcripts merged**
   (live wins for any day still on disk), so history outlives transcript cleanup.
   - Snapshots store **base topics**, so `wt map …` still reapplies **retroactively** to
     archived days.
   - It's idempotent (re-snapshotting a day just refreshes it) and tiny.
   - **Limitation:** time-scoped *overrides* are frozen at snapshot time and do **not**
     reapply to archived days (only `mappings` do). Reclassify with overrides while the
     day's transcripts still exist.

Run `wt snapshot` regularly (see [Automation](#automation)). Archived days are marked
`(archived)` in reports.

To check your current span: `wt topics` ("all time" covers everything in transcripts +
archive).

---

## Automation

Both `wt snapshot` and `wt refresh-meetings` are meant to run daily — e.g. via Claude
Code's scheduled routines (`/schedule`) or cron:

```bash
# daily, end of day
wt snapshot                   # archive yesterday and earlier
wt refresh-meetings --week    # keep this week's meetings current
```

The headless `claude -p` inside `refresh-meetings` works from cron because the `m365`
server is user-scoped — but watch for OAuth expiry (above).

---

## Configuration (`config.yaml`)

```yaml
transcripts_root: ~/.claude/projects
cursor_transcripts_root: ~/.cursor/projects   # set to null to disable
work_root: ~/work
timezone: America/New_York
default_axis: topic      # default report grouping; set to a facet (e.g. project) to group by it
gap_minutes: 15          # gap that closes a work block
min_block_seconds: 60    # credit for a lone/trailing event
meetings_file: meetings.jsonl
history_file: history.jsonl
meeting_filter:
  status: [busy]
  response: [accepted]
  allowlist: []          # recurring subjects you DO attend (bypass the filter)
idea_show_theme: nord    # Pygments style for TTY `wt idea show` (SPEC-0036)
```

---

## Files & locations

The **code** is the installable package; **config/rules** live in your XDG config dir and
**data/outputs** in your XDG data dir. Each location is overridable with an env var
(`WT_CONFIG_DIR`, `WT_DATA_DIR`, `WT_CACHE_DIR`; falls back to `XDG_*_HOME`, then the
defaults below).

```
# code (this repo)
src/wt/           the package (cli, config, paths, ingest, aggregate, report, …)
pyproject.toml    build (hatchling) + deps + the `wt` entry point
tests/            pytest suite
tools/spec_lint.py  spec validator
docs/             specs, schema, ledger, design notes

# config/rules  →  ~/.config/wt/   ($WT_CONFIG_DIR or $XDG_CONFIG_HOME/wt)
config.yaml       knobs (below)
mappings.yaml     base topic -> bucket   (rules; hand-editable or via `wt map`)
overrides.yaml    session+range -> topic (rules; hand-editable or via `wt override`)

# data/outputs  →  ~/.local/share/wt/   ($WT_DATA_DIR or $XDG_DATA_HOME/wt)
meetings.jsonl    attended meetings cache (written by refresh-meetings)
history.jsonl     durable per-day archive (written by snapshot)
reports/          markdown reports (from `wt report --md`)
exports/          tidy CSV/JSON datasets (from `wt export`)

# cache  →  ~/.cache/wt/   ($WT_CACHE_DIR or $XDG_CACHE_HOME/wt)
                  transient raw calendar dumps
```

---

## Known limitations

- Hours mix Claude's and your time and can't be cleanly separated (by design — see above).
- Overrides don't reapply to archived (snapshotted) days; mappings do.
- Meeting refresh depends on a live M365/calendar MCP connection and a non-expired OAuth token.
- Future/current-week meeting refresh counts scheduled-but-unattended meetings.
- Sub-agent (sidechain) runs count as their own concurrent streams (consistent with
  full-credit, but inflates parallelism during heavy sub-agent use).
- Not built yet: Google Sheet / JIRA-worklog export, a git-commit collector.
