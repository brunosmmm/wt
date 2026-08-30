---
id: SPEC-0015
title: Outbound portable specs + cross-project export
status: done
owner: user
created: 2026-07-16
updated: 2026-07-17
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [specs, export, ideas]
parent: SPEC-0011
depends_on: [SPEC-0013]
---

## Context

Layer 2 — the strategic payoff of the [SPEC-0011](./0011-idea-to-spec-pipeline.md) epic: `wt`
generates specs targeted at **other repos** and hands them to those repos' agents to implement.
Per the locked decisions, outbound specs are a **parallel namespace** (they must never pollute
`wt`'s own `docs/specs/` governance or `docs/LEDGER.md`), and consumption is by **file-drop**
into the target repo.

## Goals / Non-goals

**Goals**
- An outbound spec store `docs/outbox/<project>/` with its own id namespace and a light index,
  reusing the internal spec *shape* plus `target_project` / `target_repo` frontmatter.
- `wt spec new --target <project>` scaffolds an outbound spec (incl. `--from-idea`).
- `wt spec export <outbound-id> [--to <repo-path>]` file-drops a portable spec + a short
  `AGENTS.md`-style **consumption contract** into the target repo; `wt` keeps the canonical copy
  + records provenance (what was exported where, when).

**Non-goals**
- Live sync / status pull-back from the target repo (file-drop only).
- Editing the target repo beyond writing the dropped files into a chosen path.
- Reusing `docs/LEDGER.md` or the internal `spec_lint` scan for outbound specs.

## Decision

Outbound specs live under `docs/outbox/<project>/<PROJ>-NNNN-slug.md` with frontmatter that
extends the internal shape (`target_project`, `target_repo`, `source_idea`, `status`). A
separate light validator + index (`docs/outbox/INDEX.md`, generated) covers them — the internal
`tools/spec_lint.py` (which globs `docs/specs/[0-9]*.md`) is left untouched. `wt spec export`
copies the portable spec + a generated consumption contract into `--to <repo-path>` (default: a
configured per-project path) and appends a provenance record.

## Design

### Store & id namespace

- `docs/outbox/<project>/<PROJ>-NNNN-slug.md`; `<PROJ>` derived from `--target` (uppercased
  short code). `NNNN` = next free per project. A generated `docs/outbox/INDEX.md` lists outbound
  specs by project/status (its own markers; not the internal ledger).
- Config `outbox_targets`: `{ "<project>": { "repo_path": "~/work/<repo>", "spec_dir":
  "docs/specs" } }` — where exports land per project.

### Authxxing (`src/wt/specs.py`)

- `scaffold_outbound(cfg, project, *, from_idea=None, title=None) -> path` — like SPEC-0013's
  scaffold but into the outbox with `target_project`/`target_repo`; may prefill Context from an
  idea and set the reciprocal `:SPEC:` property.
- A tiny `validate_outbound(paths)` (schema + required sections) + `write_outbox_index()`.

### Export (`src/wt/export.py`, new)

- `export_spec(cfg, outbound_id, to=None) -> (dest_spec, dest_contract)`:
  - Resolve the outbound spec; `dest_root = to or outbox_targets[project]["repo_path"]`.
  - Write the **portable spec** (frontmatter trimmed to what a foreign agent needs) into
    `dest_root/<spec_dir>/`.
  - Write a **consumption contract** — a short `AGENTS.md`-style file telling the foreign agent
    how to treat the spec (authxx from it, close the loop, report back), plus the `source`
    provenance (this `wt`, the outbound id).
  - Append a provenance line to `docs/outbox/<project>/PROVENANCE.md` (what/where/when + a
    content hash) so re-exports are auditable.
- Atomic writes; never clobber an unrelated file (refuse if the dest spec exists with different
  provenance unless `--force`).

### CLI (`src/wt/cli.py`)

```
wt spec new --target thjalfi --from-idea "adversarial reviewer"   # outbound draft in outbox/
wt spec export THJALFI-0001                                        # file-drop into ~/work/thjalfi
wt spec export THJALFI-0001 --to /tmp/somerepo                     # explicit destination
```

## Alternatives considered

- **One unified spec system with a `target_project` flag** — rejected (user decision); outbound
  deliverables would pollute `wt`'s governance ledger/timeline.
- **Live/MCP consumption** — rejected for v1 (user decision); file-drop is robust, git-visible,
  and decoupled.
- **No provenance** — rejected; auditability of "what spec went to which repo when" is the point
  of keeping `wt` as the hub.

## Acceptance criteria

- [x] `wt spec new --target <project>` creates an outbound spec under `docs/outbox/<project>/`
      with `target_project`/`target_repo`, validated by the outbound validator, indexed in
      `docs/outbox/INDEX.md` — and **not** in `docs/LEDGER.md`.
- [x] `wt spec export <id> --to <path>` drops a portable spec + a consumption contract into that
      path and records provenance; a re-export without `--force` refuses to clobber divergent
      content.
- [x] `python3 tools/spec_lint.py` is unaffected by anything under `docs/outbox/` (internal scan
      untouched).

## Test plan

- **Automated:** `tests/test_export.py` (tmp outbox + tmp target dir): scaffold an outbound spec,
  export with `--to tmp`, assert the portable spec + contract + provenance exist and are
  well-formed, re-export refuses without `--force`, and `spec_lint.load_specs()`/`validate` over
  `docs/specs/` is unchanged (outbox ignored). Outbound validator + index tested directly.
- **Manual verification:** export a scaffolded outbound spec into a throwaway git repo; confirm
  the foreign agent contract reads sensibly and the spec is self-contained.
- **Regression guard:** `uv run pytest` green; internal ledger + lint untouched.

## Rollout / migration

1. Outbox store + config `outbox_targets` + outbound schema/validator + `INDEX.md`.
2. `scaffold_outbound`. 3. `src/wt/export.py` + provenance. 4. `wt spec new --target` /
`wt spec export` CLI. 5. Tests + manual; close the loop → epic done-gate.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 118 passed; `tests/test_export.py`,
      incl. internal-`spec_lint`-isolation); manual verification by the verifier (independent
      scaffold→export into a temp target: portable spec + `.contract.md` + provenance + INDEX entry;
      non-clobber refusal on a tampered hash; `--force` override).
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- Exact portable-frontmatter subset a foreign agent needs (vs. `wt`-internal fields) — pin down
  during implementation with one real target repo.

## What shipped / deviations

Implemented as designed, with these concrete choices:

- **Config:** `outbox_targets` added to `DEFAULT_CONFIG` (default `{}`); `outbox_dir` is
  injectable on `cfg` for tests/CLI (defaults to `Path.cwd()/docs/outbox`).
- **`src/wt/specs.py`:** `outbox_dir`, `_proj_code`, `next_outbound_number`,
  `scaffold_outbound`, `validate_outbound`, `write_outbox_index` — all built the same way as the
  SPEC-0013/0014 helpers they sit beside (reuse `_spec_lint()`'s `split_frontmatter`/`sections`
  for parsing only, never its `jsonschema` schema, since outbound `id` is `PROJ-NNNN` not
  `SPEC-NNNN`). `docs/outbox/INDEX.md` uses its own `<!-- outbox:begin/end -->` markers,
  regenerated on every `scaffold_outbound`.
- **`src/wt/export.py` (new):** `export_spec(cfg, outbound_id, to=None, force=False)`. The
  portable spec's frontmatter is trimmed to
  `id/title/status/owner/created/updated/kind/tags/depends_on` (dropping
  `target_project`/`target_repo`/`source_idea`, which are `wt`-internal routing, not useful to
  a foreign agent) plus two provenance fields embedded directly in the dest file:
  `source_outbound_id` and `source_content_hash` (a 16-hex-char sha256 of `outbound_id` + the
  spec body, independent of the frontmatter it's embedded in). The non-clobber guard compares
  those two fields against a freshly computed hash: identical → idempotent re-export always
  allowed; different (or absent) → refuse unless `--force`. The consumption contract is written
  alongside the spec as `<same-stem>.contract.md` (not a shared `AGENTS.md`, to keep exports
  from multiple specs in one target dir from colliding). Provenance is appended to
  `docs/outbox/<project>/PROVENANCE.md` as one line per export (timestamp, outbound id, dest
  path, hash, `--force` flag if used).
- **CLI:** `wt spec new --target <project> [--from-idea <sel>] [--title T]` (mutually
  exclusive-ish with the original `--from-idea`-only internal path — `--target` present routes
  to `scaffold_outbound`; otherwise the pre-existing SPEC-0013 behavior, still requiring
  `--from-idea`) and `wt spec export <outbound-id> [--to PATH] [--force]`.
- **Real repo artifacts added:** `docs/outbox/README.md` (store explainer) and a generated,
  empty `docs/outbox/INDEX.md` (`_No outbound specs yet._`) — no scaffolded/test fixtures left
  in the real store.
- **Verified:** `uv run pytest` (118 passed, incl. new `tests/test_export.py`, 17 tests) and
  `python3 tools/spec_lint.py` (18 specs OK) both green; a dedicated test
  (`test_internal_spec_lint_unaffected_by_outbox`) asserts the real `docs/specs/` scan is
  unaffected. Manual verification: `wt spec new --target demoproj` → `wt spec export
  DEMOPROJ-0001 --to <tmp target repo>` produced a well-formed portable spec + contract +
  `PROVENANCE.md`; re-export after hand-editing the dest's `source_content_hash` refused with
  "different provenance" (exit 1), and `--force` then overwrote cleanly.

**Location revised by [SPEC-0021](./0021-outbox-in-data-dir.md):** the outbox default moved
from `docs/outbox/` (in the wt repo) to `<data_dir>/outbox` (user data) — outbound specs are
content for other projects and don't belong in wt's own git. The rest of SPEC-0015 stands.
