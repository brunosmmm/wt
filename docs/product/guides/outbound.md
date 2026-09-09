# Outbound

Ship work into **another** project’s repo. The governing portable lives in that tree;
wt’s outbox keeps a copy and lifecycle on the idea.

## Register the project

```bash
wt projects --json                          # name → research / outbound
wt projects add Example --repo ~/work/example   # prints plan; does not write
wt projects add Example --repo ~/work/example --yes
```

`repo_path` is both the export destination and the **explore research root** for that
project. Stubs without a repo stay `outbound: false` until you add one.

## Capture with `:PROJECT:`

```bash
wt idea "…" --project Example
# explore Summary / Log as usual — research root follows the project
wt spec new --from-idea IDEA-00N            # lands under data_dir/outbox/<project>/
```

Force an internal SPEC in this repo instead: `--internal`.

## After `accepted`

Do **not** `wt spec generate` on outbound portables.

```bash
wt spec export PROJ-NNNN                    # idea → EXPORTED; file in target docs/specs/
# In the target repo: implement against the portable (status + AC + Test plan)
# Prefer /wt-implement-spec if skills are installed there
wt spec pull-status PROJ-NNNN               # optional: mirror status → outbox
# when portable is done → idea SHIPPED (pull-status / sweep)
```

Schemes (e.g. REMOVED): `wt spec schemes`, then
`wt spec export … --scheme …` as needed.

## Fit after ship

```bash
wt spec fit-log PROJ-NNNN --note "…"
```

Outbound AC should include a human outcome (“I can …”) when possible.

See also [Projects](../capabilities/projects.md) and [Multi-project](multi-project.md).
