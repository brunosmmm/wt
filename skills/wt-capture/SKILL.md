---
name: wt-capture
description: "Capture a quick idea into wt without breaking flow. Use when a thought is a seed for future work (not yet an actionable task) and you want it durably recorded."
trigger: capturing a stray idea/thought while working
---

# wt-capture

## When to use

A thought crosses your mind that's a **seed, not a task** — no clear next action yet, just
worth not losing. If it's already **actionable** (you could do it today as a TODO), use
`wt add` instead (see `AGENTS.md` / `wt add --help`); ideas and tasks are different
lifecycles (SPEC-0091).

If the idea was **already shaped in this conversation** and you need to distill that chat into
a durable idea (title + optional Summary/Log), use `/wt-seed` instead.

## Procedure

1. **Optional related check:** if the thought might already exist, run `/wt-related`
   (`wt ideas --query "…" --json`; see `wt ideas --help`) before capturing.
2. **Multi-project check (SPEC-0095):** if the one-liner clearly spans ≥2 products/repos, prefer
   `/wt-seed` (conversation → project-map preview) over a single bare `wt idea`. Or capture an
   umbrella title and immediately explore with a project map — do not pretend one `:PROJECT:`
   owns the whole stack.
3. Capture it: `wt idea "<the thought>"`. Run `wt idea --help` for the exact flag syntax
   (state override, tags, priority, `--kind`). Prefer `--state INCUBATE` if you know you'll
   explore soon. Use `--kind improvement|chore` when the capture is clearly that shape
   (default `idea`). **`--kind bug`:** prefer `wt add` for actionable defects; if the bug
   needs explore→spec (design/systemic), pass `--force-idea` (or accept the soft warn and
   keep the idea). Kind remains a triage label — same pipeline as ideas (SPEC-0044/0091).
4. Tag conventions: use `--tag` to group related ideas so `wt ideas` triage later is easy.
5. Leave it — **do not** promote yet.

## Conventions / guardrails

- A sentence or two is enough at capture time.
- **Next:** durable enrichment is `/wt-explore` (`wt idea summary|log|…`), not promotion.
- Conversation already rich → `/wt-seed` (preview + optional enrichment in one pass).
- Promotion (`/wt-new-work`) is only after Summary is non-empty and you're ready for an
  accepted governing spec.

## Verify

`wt ideas` shows the new idea. `wt next` will usually say `wt idea log …` until Summary
exists.
