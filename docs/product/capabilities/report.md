# Report & topics

Passive hours from transcripts (and meetings). No timer for this signal.

## When to use

Weekly review, mapping unknown topics, exporting a tidy dataset, preserving history
before Claude deletes transcripts.

## Commands

| Command | Role |
|---------|------|
| `wt` | Dashboard: today + this week (`--split` diagnostic) |
| `wt report` | Per-topic hours; `--week`, `--by AXIS`, `--last N`, `--md` |
| `wt topics` | Base topics + hours + facets; `--unmapped` |
| `wt map` | Attach facets: `wt map RAW project=Name` |
| `wt override` | Time-scoped reclassification for one session span |
| `wt review` | Segment timeline, unclassified inbox; `--fix` |
| `wt snapshot` | Archive past days to `history.jsonl` |
| `wt export` | CSV/JSON dataset of date/topic/hours/facets |
| `wt digest` | Hours joined to org tasks by JIRA key |

Workflow: [Track time](../guides/track-time.md).
