---
id: SPEC-0159
title: "Outbox project rename / migrate (dry-run default)"
status: accepted
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
tags: [outbox, migration, cli]
depends_on: [SPEC-0137]
source_idea: IDEA-397
---

## Context

Promoted from `IDEA-397`. Renaming/extracting an outbound project has no first-class
tool. Motivating case: DemoCo branding → DemoCo / `demo-generator`. Retargeting
`repo_path` is already covered by SPEC-0137 (`wt projects add … --yes`); what is missing
is **bucket rename** (config key + outbox directory + idea routing), with a safe dry-run
default.

Explore (pass 1) confirmed: no migrate/rename API exists; `plan_project_add` /
`apply_project_add` only update the **same** key; outbound id lookup globs across dirs but
`write_outbox_index` groups by directory name; live DemoCo footprint is large (~33 ideas,
many `DEMO-*` portables).

## Goals / Non-goals

**Goals**

- `wt projects rename OLD NEW` (name flexible) that **plans by default** and applies only
  with explicit confirmation.
- v1 moves: `outbox_targets[OLD]→[NEW]`, rename `<data_dir>/outbox/OLD` → `…/NEW`, rewrite
  idea `:PROJECT:` (active + archive when on `org_files`), rename `** Ext OLD` →
  `** Ext NEW`, rename `idea_extensions[OLD]` config key if present, regenerate outbox INDEX.
- Fail closed on conflicts; backup `config.yaml` (existing `.bak.<ts>` pattern); print an
  apply summary with counts.

**Non-goals (v1)**

- Rekeying outbound ids (`DEMO-NNNN` → `ENC-NNNN`) or rewriting filenames / FM `id` /
  `parent:`.
- Rewriting portables or `target_spec_path` inside the **target** git repo.
- Sheet row remapping / mappings.yaml facet rename / body-text epic-id scrubbing.
- Changing export/promote semantics or mint rules beyond “future mints follow new bucket”.
- Interactive TUI.

## Decision

Ship a **plan/apply rename** beside SPEC-0137’s add path:

1. **Dry-run is the default.** Printing the plan never writes.
2. **Apply requires `--yes`** (same contract as `projects add`). No silent writes.
3. **v1 = bucket rename without id rekey.** Existing `DEMO-*` (etc.) ids remain valid
   under the new directory; documentation must state that future mints use
   `_proj_code(NEW)`.
4. **Target-repo portable rewrite is out of v1** — frozen `target_spec_path` makes a
   same-command rewrite unsafe without rekey; leave a clear “v2 / second command” hook.
5. New module (e.g. `src/wt/outbox_migrate.py`) + CLI under `wt projects`, reusing
   `apply_project_add`’s user-config load/backup/atomic write patterns rather than
   overloading add.

## Design

### CLI

```text
wt projects rename OLD NEW           # print plan (exit 0 if viable)
wt projects rename OLD NEW --yes     # apply plan
```

Plan output (human): old→new, config path, outbox dir rename, idea rewrite counts
(active/archive), Ext / `idea_extensions` hits, INDEX refresh, warnings (sheet configured,
nonempty `target_spec_path` samples, id-prefix ≠ `_proj_code(NEW)`).

JSON optional later; not required for AC.

### Plan / apply API

```python
# src/wt/outbox_migrate.py (name may vary)
def plan_project_rename(cfg, old: str, new: str) -> dict: ...
def apply_project_rename(cfg, plan: dict) -> dict: ...
```

**Plan checks (fail closed before apply):**

- `old` exists in `outbox_targets` (or as an on-disk outbox dir with ideas — prefer requiring
  config key; document if dir-only orphans are warned).
- `new` does not already exist as an `outbox_targets` key or outbox directory.
- `new` is a safe path segment (no `/`, not empty).
- No two outbound files would collide after a future rekey (v1: N/A); warn if `_proj_code(old)
  != _proj_code(new)` so operators know mint prefix will change.

**Apply order:**

1. Backup user `config.yaml` → `config.yaml.bak.<ts>` (same as `apply_project_add`).
2. Rewrite config: pop `outbox_targets[old]`, set `[new]`; rename `idea_extensions[old]` if
   present.
3. `Path.rename` outbox directory when it exists; if missing, warn and continue (config-only
   rename).
4. Bulk idea property updates via existing org writers (`set_idea_project` / `set_property` /
   Ext rename helper — **add** Ext headline rename if absent today).
5. Include archive file when it is part of the loaded org corpus.
6. `write_outbox_index(cfg)`.
7. Print summary; optional note suggesting `wt spec reconcile` (do not hard-fail on
   reconcile noise).

### Idea / Ext surfaces

| Field | v1 action |
|-------|-----------|
| `:PROJECT:` | `old` → `new` |
| `** Ext <old>` | Rename headline to `** Ext <new>` (values preserved) |
| `:SPEC:` / `:EPIC:` | **Leave** (still `DEMO-*` until v2) |
| `:TARGET_*` | **Leave** (document stale-path caveat) |
| FM `target_project` in outbox markdown | Update to `new` (keeps export routing keyed to bucket) |
| FM `id` / filename | **Leave** |

### Docs

- Short section on [Outbound](../product/guides/outbound.md) and/or projects capability:
  rename vs `projects add` retarget; v1 id caveat; pointer to v2 rekey.

## Alternatives considered

- **Full id rekey in v1** — rejected: large blast radius (filenames, FM parent graphs,
  target-repo `source_outbound_id`, PROVENANCE, Summary text). Ship bucket rename first.
- **Overwrite `projects add` to mean rename** — rejected: add is create/update same key
  (SPEC-0137); rename is a different hazard class.
- **Always rewrite target-repo portables** — rejected until rekey exists; frozen
  `target_spec_path` would strand exports.

## Acceptance criteria

- [ ] `wt projects rename OLD NEW` without `--yes` writes nothing and prints a viable plan
      (or a clear conflict error).
- [ ] `wt projects rename OLD NEW --yes` renames `outbox_targets` key, outbox directory (if
      present), idea `:PROJECT:` (and Ext headline / `idea_extensions` when present), updates
      outbox FM `target_project`, regenerates INDEX, and leaves outbound ids unchanged.
- [ ] Conflicts (missing OLD, existing NEW, unsafe name) abort with nonzero exit and no
      partial config write (backup restored or never replaced).
- [ ] Automated tests cover dry-run purity, happy-path apply, and at least one conflict.
- [ ] Product docs mention rename vs repo retarget and the “ids unchanged in v1” caveat.
- [ ] `python3 tools/spec_lint.py` clean; ledger lists SPEC-0159 accepted.

## Test plan

- **Automated:** `tests/test_outbox_migrate.py` (or adjacent) with tmp config/data/org —
  dry-run leaves disk untouched; apply renames dir + config + one idea’s `:PROJECT:`/Ext;
  conflict when `NEW` exists.
- **Manual:** against a throwaway copy of DemoCo→DemoCo names (or tmp fixture): plan,
  then `--yes`, `wt projects list --json`, `wt ideas --project NEW --json`, open INDEX.
- **Regression:** `projects add` still works; export/pull-status on an unrekeyed id under
  the new folder still resolves via id glob.

## Rollout / migration

Land behind the new CLI verb. Operators rename DemoCo→DemoCo after install. Id rekey
remains a follow-up spec/idea. No automatic migration of existing installs.

## Definition of done

- [ ] Acceptance criteria all met.
- [ ] Test plan executed; `uv run pytest` green; manual steps noted.
- [ ] Spec body matches what shipped.
- [ ] `docs/LEDGER.md` regenerated; IDEA-397 questions decided by this spec resolved.

## Open questions

- None blocking accept — v2 id rekey / target-repo rewrite tracked as follow-up work when
  needed (can spawn from IDEA-397 log or a child idea).
