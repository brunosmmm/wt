#!/usr/bin/env python3
"""Probe: knob sensitivity + non-keyed-branch mapping load over all transcripts.

Eastern-TZ day boundaries. Reports, for each gap threshold:
  - total billed (concurrent sum) vs wall-clock (union) hours across all data
Then, at the chosen gap, how much time sits on JIRA-keyed vs non-keyed topics
(i.e. how much manual mapping you'd actually face).
"""
import json, re, glob, os
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.expanduser("~/.claude/projects")
EAST = ZoneInfo("America/New_York")
MIN_BLOCK = 60
KEY_RE = re.compile(r"([A-Z]{2,}-\d+)")

def repo_of(cwd):
    if not cwd: return "?"
    p = cwd.split("/")
    if "work" in p:
        i = p.index("work")
        if i+1 < len(p): return p[i+1]
    return p[-1] or "?"

def topic_of(cwd, branch):
    branch = branch or ""
    m = KEY_RE.search(branch.upper())
    if m: return m.group(1), True
    repo = repo_of(cwd); b = branch.split("/")[-1] if branch else ""
    return (repo if b in ("main","master","HEAD","") else f"{repo}:{b}"), False

def parse_ts(s):
    try: return datetime.fromisoformat(s.replace("Z","+00:00"))
    except Exception: return None

# load streams once
streams = []
for path in glob.glob(os.path.join(ROOT,"**","*.jsonl"), recursive=True):
    ev=[]
    try:
        with open(path) as fh:
            for line in fh:
                try: o=json.loads(line)
                except Exception: continue
                ts=o.get("timestamp")
                if not ts: continue
                t=parse_ts(ts)
                if t: ev.append((t,o.get("cwd"),o.get("gitBranch")))
    except Exception: continue
    if ev:
        ev.sort(key=lambda e:e[0]); streams.append(ev)

def blocks_for_gap(gap_s):
    """yield (start,end,cwd,branch) blocks across all streams."""
    out=[]
    for ev in streams:
        bs=ev[0][0]; prev=ev[0][0]; cwd,br=ev[0][1],ev[0][2]
        for t,c,b in ev[1:]:
            if (t-prev).total_seconds()>gap_s:
                out.append((bs,prev,cwd,br)); bs=t
            prev,cwd,br=t,(c or cwd),(b or br)
        out.append((bs,prev,cwd,br))
    return out

def union_secs(intervals):
    if not intervals: return 0.0
    iv=sorted(intervals); tot=0.0; cs,ce=iv[0]
    for s,e in iv[1:]:
        if s<=ce: ce=max(ce,e)
        else: tot+=(ce-cs).total_seconds(); cs,ce=s,e
    tot+=(ce-cs).total_seconds(); return tot

print(f"streams={len(streams)}\n")
print("=== KNOB SENSITIVITY (whole dataset, Eastern days) ===")
print(f"{'gap':>6} {'blocks':>8} {'billed(h)':>11} {'wall(h)':>9} {'ratio':>6}")
for gap_min in (10,15,30):
    blks=blocks_for_gap(gap_min*60)
    billed=sum(max((e-s).total_seconds(),MIN_BLOCK) for s,e,_,_ in blks)
    wall=union_secs([(s,e) for s,e,_,_ in blks])
    print(f"{gap_min:>4}m  {len(blks):>8} {billed/3600:>11.1f} {wall/3600:>9.1f} {billed/wall:>6.2f}")

print("\n=== TOPIC / MAPPING LOAD (gap=15m) ===")
blks=blocks_for_gap(15*60)
topic_secs=defaultdict(float); keyed=set()
for s,e,cwd,br in blks:
    tp,isk=topic_of(cwd,br)
    topic_secs[tp]+=max((e-s).total_seconds(),MIN_BLOCK)
    if isk: keyed.add(tp)
total=sum(topic_secs.values())
keyed_h=sum(v for k,v in topic_secs.items() if k in keyed)/3600
nonkeyed_h=(total/3600)-keyed_h
print(f"distinct topics: {len(topic_secs)}   keyed(JIRA): {len(keyed)}   non-keyed: {len(topic_secs)-len(keyed)}")
print(f"time on keyed: {keyed_h:.1f}h ({100*keyed_h/(total/3600):.0f}%)   non-keyed: {nonkeyed_h:.1f}h ({100*nonkeyed_h/(total/3600):.0f}%)")
print("\nnon-keyed topics by hours (these are what you'd manually map):")
for tp,sec in sorted(((k,v) for k,v in topic_secs.items() if k not in keyed), key=lambda kv:-kv[1]):
    print(f"   {sec/3600:6.1f}h  {tp}")
print("\nkeyed topics:")
for tp,sec in sorted(((k,v) for k,v in topic_secs.items() if k in keyed), key=lambda kv:-kv[1]):
    print(f"   {sec/3600:6.1f}h  {tp}")
