# Track time

wt’s primary time signal is **passive**: Claude Code and Cursor transcripts (plus Outlook
meetings). You do not start a timer for that. Org `clock-in` / `clock-out` is
**supplemental** wall-time on an idea while you build a slice — see [Clock](../capabilities/clock.md).

## Weekly loop

1. **See what landed**

   ```bash
   wt                      # dashboard
   wt report --week        # this week by topic
   wt report --week --by project
   ```

2. **Name the unknowns**

   ```bash
   wt topics --unmapped
   wt map <raw-topic> project=Name area=…
   ```

   Facets (`project=`, `area=`, …) are how reports group. Bare `wt map topic value` sets
   `bucket=`.

3. **Sanity-check segments**

   ```bash
   wt review --week        # timeline + unclassified; --fix maps interactively
   ```

4. **Keep history**

   Claude Code deletes old transcripts. Archive before they vanish:

   ```bash
   wt snapshot             # through yesterday by default
   ```

5. **Meetings (optional)**

   ```bash
   wt refresh-meetings --week
   ```

## Date scopes

Same pattern on `report`, `review`, `agenda`, `digest`, `refresh-meetings`:

```bash
wt report                 # today
wt report --week          # this week
wt report 2026-06-01      # that day
wt report -w 2026-06-01   # week containing that date
wt report --last 7
```

## Export / share

```bash
wt export --week --format csv -o week.csv
```

## What “hours” mean

- Engagement wall-clock per topic (generation + your reading/typing fused).
- Concurrent sessions can make *billed* topic hours exceed real wall-clock; the report
  also shows de-duplicated wall-clock and a parallelism ratio.

Deep background: [Time model & retention](../concepts/time-and-retention.md).

Next: [Idea → ship](idea-to-ship.md) when a time topic becomes work to govern.
