# Meetings

Outlook (M365) meetings feed the same hours pipeline as transcripts.

## Commands

```bash
wt refresh-meetings              # today
wt refresh-meetings --week
wt refresh-meetings --days N
wt ingest-meetings RAWFILE       # filter a raw calendar JSON dump
```

`refresh-meetings` pulls via the configured headless Claude + m365 MCP path into
`meetings.jsonl`. After refresh, hours show up in `wt` / `wt report` like any other
source. Date scopes match [Track time](../guides/track-time.md).
