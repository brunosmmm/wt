# Workflow architecture

How wt pieces connect. These are **workflow** diagrams (not code design). Diagram DSL is
Mermaid for now (SPEC-0148); D2 can replace the fences later without changing the story.

## Dual systems

```mermaid
flowchart LR
  subgraph Passive["Passive time"]
    T[Transcripts / meetings] --> H[Hours by topic]
    H --> R[wt report / topics / map]
  end
  subgraph Ship["Idea → ship"]
    I[wt idea] --> E[Explore]
    E --> S[Accepted spec]
    S --> G[Generate or export]
    G --> V[Verify / SHIPPED]
  end
  Clock[Supplemental clock-in] -.-> Ship
  Passive --- Ship
```

Passive hours and idea→ship share the CLI and triage surfaces; clock-in is optional wall-time
on an idea while you build.

## Idea → ship (internal)

```mermaid
sequenceDiagram
  participant U as You / agent
  participant CLI as wt CLI / desk
  participant Spec as docs/specs
  participant Org as org tasks
  U->>CLI: wt idea "…"
  U->>CLI: summary / log / questions
  U->>CLI: wt spec new --from-idea
  U->>Spec: authxx Decision + AC + Test plan
  U->>Spec: status accepted
  U->>CLI: wt spec generate
  CLI->>Org: tasks
  U->>CLI: implement + clock-in/out
  U->>CLI: wt spec verify / done
```

## Outbound

```mermaid
flowchart TD
  A[Idea with :PROJECT:] --> B[Outbox portable]
  B --> C[status accepted]
  C --> D[wt spec export]
  D --> E[Target repo docs/specs]
  E --> F[Implement portable]
  F --> G[wt spec pull-status / sweep]
  G --> H[Idea SHIPPED]
```

## Desk vs CLI

```mermaid
flowchart LR
  CLI[wt ideas / next / hub --json] -->|agents + scripts| Work
  Desk[wt tui IdeaDesk] -->|humans| Work[Explore / metadata / clock]
  Work --> Specs[Specs + tasks]
```

See [Idea → ship](../guides/idea-to-ship.md), [Track time](../guides/track-time.md), and
[Outbound](../guides/outbound.md) for command-level walkthroughs with live SVG captures.

Storage topology and DoD: [Architecture](architecture.md) · [Lifecycle](lifecycle.md).
