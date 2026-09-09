# Multi-project

When a conversation or epic spans **more than one** tracked repo, do not collapse
everything under a single `:PROJECT:`.

## Map first

```bash
wt projects --json
```

Confirm which names are internal (this wt checkout / Meta-Tools) vs outbound
(`repo_path` set). Unknown paths → [Outbound](outbound.md) registration
(`wt projects add …` dry-run, then `--yes`).

## Fan out

1. Capture / promote an **epic** for the cross-cutting story (often Meta-Tools or the
   coordinating project).
2. Seed **child ideas** with `(project: Name)` in the title or explicit `--project`.
3. Each child gets its own spec routing (internal SPEC-NNNN vs outbox PROJ-NNNN).
4. Explore and implement per child; do not write one Summary that pretends one research
   root covers all repos.

`wt next` / hub will show the fan-out as separate rows — that is intentional.

## Soft rules

- Naming ≥2 projects or paths in a chat → preview the project map before locking Summary.
- Soft-warn if you continue a single-root explore anyway.
- Incomplete epics: extend with `/wt-rework` (scaffold children), not ad-hoc tasks only.

Back to [Idea → ship](idea-to-ship.md) or [Outbound](outbound.md) per child.
