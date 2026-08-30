#!/usr/bin/env python3
"""Throwaway prototype: infer active work blocks from Claude Code transcripts.

Proves the passive-tracking concept end-to-end on real data:
  - one "session stream" = one transcript file (a session, or a subagent sidechain)
  - gap-threshold block inference: consecutive events <GAP apart = one block
  - topic = JIRA key from gitBranch if present, else  repo:branch
  - concurrent credit: streams bill independently, so daily sums can exceed
    real wall-clock (which is exactly what we want)
"""
import json, re, glob, os, sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.expanduser("~/.claude/projects")
GAP_SECONDS = 15 * 60          # gap that closes a block
MIN_BLOCK_SECONDS = 60         # a lone event counts as 1 min
KEY_RE = re.compile(r"([A-Z]{2,}-\d+)")

def repo_of(cwd):
    if not cwd:
        return "?"
    parts = cwd.split("/")
    # /home/user/work/<repo>/...  -> <repo>; else last meaningful component
    if "work" in parts:
        i = parts.index("work")
        if i + 1 < len(parts):
            return parts[i + 1]
    return parts[-1] or "?"

def topic_of(cwd, branch):
    branch = branch or ""
    m = KEY_RE.search(branch.upper())
    if m:
        return m.group(1)                      # JIRA key wins
    repo = repo_of(cwd)
    b = branch.split("/")[-1] if branch else ""
    if b in ("main", "master", "HEAD", ""):
        return repo                            # trunk work -> just the repo
    return f"{repo}:{b}"

def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

# per stream: list of (ts, cwd, branch)
streams = []
for path in glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True):
    events = []
    try:
        with open(path) as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                ts = o.get("timestamp")
                if not ts:
                    continue
                t = parse_ts(ts)
                if t:
                    events.append((t, o.get("cwd"), o.get("gitBranch")))
    except Exception:
        continue
    if events:
        events.sort(key=lambda e: e[0])
        streams.append(events)

# day -> topic -> seconds ; and day -> set of (start,end) intervals for wall-clock union
day_topic = defaultdict(lambda: defaultdict(float))
day_intervals = defaultdict(list)

for events in streams:
    block_start = events[0][0]
    prev = events[0][0]
    cwd, branch = events[0][1], events[0][2]
    def flush(start, end, cwd, branch):
        secs = max((end - start).total_seconds(), MIN_BLOCK_SECONDS)
        day = start.astimezone(timezone.utc).date().isoformat()
        day_topic[day][topic_of(cwd, branch)] += secs
        day_intervals[day].append((start, end))
    for t, c, b in events[1:]:
        if (t - prev).total_seconds() > GAP_SECONDS:
            flush(block_start, prev, cwd, branch)
            block_start = t
        prev, cwd, branch = t, (c or cwd), (b or branch)
    flush(block_start, prev, cwd, branch)

def union_hours(intervals):
    if not intervals:
        return 0.0
    intervals = sorted(intervals)
    total = 0.0
    cs, ce = intervals[0]
    for s, e in intervals[1:]:
        if s <= ce:
            ce = max(ce, e)
        else:
            total += (ce - cs).total_seconds(); cs, ce = s, e
    total += (ce - cs).total_seconds()
    return total / 3600

print(f"GAP={GAP_SECONDS//60}min  streams={len(streams)}\n")
for day in sorted(day_topic)[-6:]:
    topics = day_topic[day]
    billed = sum(topics.values()) / 3600
    wall = union_hours(day_intervals[day])
    print(f"{day}   billed(sum, concurrent)={billed:5.1f}h   wall-clock(union)={wall:5.1f}h")
    for topic, secs in sorted(topics.items(), key=lambda kv: -kv[1]):
        print(f"     {secs/3600:5.2f}h  {topic}")
    print()
