---
name: wt-related
description: "Search open and closed ideas for related prior work before capturing or promoting. Use when a new thought might already exist as an idea (or a closed one)."
trigger: checking for duplicate/related ideas before capture or promote
---

# wt-related

## When to use

Before `/wt-capture`, `/wt-seed`, or `/wt-new-work`, when the thought might already live in the
idea corpus (including PROMOTED / EXPORTED / DROPPED / RESEARCHED / archived). Prefer this over
eyeballing `wt ideas` or shelling `wt idea show` in a loop.

## Procedure

1. Distill 2–6 distinctive tokens from the thought (project jargon, verbs, nouns — not filler).
2. Search: `wt ideas --query "…" --json`. Exact flags (`--limit`, `--state`, `--kind`):
   `wt ideas --help`. `--query` already searches the full idea corpus (open + closed).
3. Read hits (`id`, `state`, `score`, `snippet`, `heading`). For anything close, open it with
   `wt idea show <id>` (or `--json`).
4. Act:
   - Close duplicate / fold → enrich or close the existing idea (`wt idea --help`); do **not**
     mint a twin.
   - Related but distinct → capture/promote as planned; optionally mention the relative in Log.
   - No hits → proceed with capture / seed / new-work.

## Conventions / guardrails

- Ideas-only: this is not a substitute for org-task search.
- Do not treat tag filters as search — use `--query` for discovery; `--kind` / `--state` only
  to narrow.
- Never invent hits; trust the JSON list (empty list = no match, exit 0).

## Verify

`wt ideas --query "…" --json` prints `wt.ideas.search.v1` with a (possibly empty) `ideas`
array. Each hit has `score` and `snippet`.
