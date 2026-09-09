# Concepts

Core vocabulary used across wt guides. Prefer these terms in product docs; link SPECs only when explaining *why*.

| Term | Meaning |
|------|---------|
| **Topic** | Unit of passive time — usually a repository, sometimes refined to a JIRA key. |
| **Facet / mapping** | Human label on a topic (`project=…`, `area=…`) in `mappings.yaml`. |
| **Override** | One-off time-range reclassification of a session. |
| **Idea** | Org headline in the ideas file (`IDEA-NNN`) — a parked or incubating thought. |
| **Summary / Log / questions** | Enrichment on an idea; Summary gates promotion. |
| **Spec** | Numbered design doc (`SPEC-NNNN` or outbound `PROJ-NNNN`) with lifecycle + AC. |
| **Ledger** | Index of specs (`docs/LEDGER.md`). |
| **Internal** | Spec lives in this wt repo; `wt spec generate` → org tasks → `PROMOTED`. |
| **Outbound** | Spec lives under data-dir outbox; `wt spec export` → target repo portable. |
| **Portable** | Exported markdown spec in a foreign repo (`docs/specs/PROJ-*.md`). |
| **Hub** | Read-only triage JSON/CLI across ideas + active specs (`wt hub`). |
| **Desk / TUI** | Interactive ideas UI (`wt tui`). |
| **Project (association)** | `:PROJECT:` on an idea — routes research root and outbound vs internal. |
| **Clock-in** | Supplemental org `CLOCK:` on an idea for intentional build sessions. |
| **Passive tracking** | Hours inferred from transcripts/meetings — no start/stop timer. |
| **Skill** | Agent playbook (`/wt-orient`, `/wt-explore`, …) installed via `wt skills`. |
| **Sheet sync** | Optional Google Sheet triage loop for a configured project. |

Longer notes: [Time model & retention](time-and-retention.md).

See also [Guides](../guides/index.md) and [Capabilities](../capabilities/index.md).
