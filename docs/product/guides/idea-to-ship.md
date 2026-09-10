# Idea → ship

Turn a parked thought into finished work **inside this repo** (Meta-Tools / no outbound
project). For another codebase, use [Outbound](outbound.md).

## Pipeline

```
capture → explore → author accepted spec → generate tasks → build → verify
```

Full picture (roles and handoffs): [Workflow architecture](../concepts/workflows.md).
On-disk shape (Summary / questions / Log, rotation, archive): [Org-mode storage](org-storage.md).

After capture, triage looks like this:

![wt ideas](../assets/captures/cli-ideas.svg)

![wt next](../assets/captures/cli-next.svg)

| Step | Human CLI | Agent skill (optional) |
|------|-----------|------------------------|
| Capture | `wt idea "…"` | `/wt-capture`, `/wt-seed` |
| Enrich | `wt idea summary\|log\|questions` | `/wt-explore` |
| Related? | `wt ideas --query …` | `/wt-related` |
| Spec | `wt spec new --from-idea …` | `/wt-new-work` |
| Tasks | `wt spec generate SPEC-NNNN` | `/wt-generate` |
| Done? | `wt spec verify` / ledger | `/wt-verify` |

`wt next` (and `wt ideas --json`) recommend the next command per idea.

## Capture vs task

Ideas are **seeds**. Actionable one-offs are tasks:

```bash
wt idea "systemic gate design" --project Meta-Tools
wt add "fix the flaky CI gate" --project Meta-Tools
```

## Explore before promote

Do not promote an empty idea. Put durable notes on it first:

```bash
wt idea summary IDEA-00N --set "…"
wt idea log IDEA-00N "what we learned"
wt idea show IDEA-00N
wt idea mark-explored IDEA-00N   # when Summary is ready
```

States that matter: `IDEA` / `INCUBATE` → exploring; `SPECCED` → draft/accepted spec;
`PROMOTED` → org tasks exist. See [Concepts](../concepts/index.md).

## Accept, then generate

1. `wt spec new --from-idea IDEA-00N --internal` (or routing default for Meta-Tools).
2. Fill Decision / Design / Acceptance criteria / **Test plan**.
3. Set frontmatter `status: accepted`.
4. `python3 tools/spec_lint.py --write-ledger`
5. `wt spec generate SPEC-NNNN` → idea becomes **PROMOTED**.
6. Implement; clock with `wt idea clock-in` / `clock-out` while you work the slice.
7. Close the loop: tests + AC true + `status: done` + ledger — `/wt-verify` or
   `wt spec verify`.

If the design is wrong: `/wt-rework` (supersede), do not silently rewrite past `draft`.

## Triage rhythm

```bash
wt ideas
wt agenda
wt next
wt hub                 # union of ideas + specs + outbox
```

Optional desk: `wt tui` ([Desk](../capabilities/tui.md)).

Next: [Outbound](outbound.md) when `:PROJECT:` points at another repo.
