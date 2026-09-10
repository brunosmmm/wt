---
id: SPEC-0130
title: "Worktree-aware portable spec resolution for pull_status/pull_clock"
status: done
owner: user
created: 2026-08-06
updated: 2026-08-06
source_idea: IDEA-235
milestone: "M3: idea→spec pipeline"
tags: [export, worktree, bugfix]
---

## Context

Promoted from idea `IDEA-235` (wt spec sweep/pull_status can't find a portable spec that only exists in a sibling git worktree of the target repo).

  :PROPERTIES:
  :ID: IDEA-235
  :CREATED: [2026-08-06 Thu 20:16]
  :UPDATED: [2026-08-06 Thu 20:36]
  :PROJECT: Meta-Tools
  :KIND: bug
  :EXPLORED: 1
  :EXPLORED_AT: [2026-08-06 Thu 20:18]
  :END:
** Summary
CORRECTED after actually testing every example from the original `wt spec sweep` output (not
just one) -- the initial worktree hypothesis was wrong for the overwhelming majority of cases.
Real breakdown of the ~20 "missing" lines, checked one by one:

- **18 of ~20**: NOT a worktree-discovery problem at all. Two sub-causes, both now moot (fixed
  by hand this session, no code change involved): (a) ~15 Example specs were deliberately
  stripped from their PRs by an explicit team convention ("keep governing specs in wt outbox;
  this repo PR is code/dashboard only") -- the content was never actually lost since wt's own
  outbox always held the authxxitative copy; (b) a couple (`PROJ-0001`,
  `DEMO-0029`, plus `EXAMPLE-0006`) simply had never had `wt spec export` run for
  them at all -- `status: accepted` frozen since scaffold time, zero git history anywhere.
  Resolved by re-running `wt spec export <id> --to <repo>` for all of them (dumped as local,
  uncommitted files, no branch touched) -- `wt spec sweep` is now fully clean, zero missing.
- **1 of ~20** (`EXAMPLE-0026`): the ONLY genuine instance of the original hypothesis --
  `IDEA-212`'s portable spec existed only in a sibling git worktree (`example-ats-1`, checked
  out to the still-unmerged branch `user/EXAMPLE-0026-stream-observer`), not at
  `outbox_targets.Example.repo_path`'s configured path. This one is a real, narrow case where
  `_portable_dest_path`/`pull_status`/`sweep` (SPEC-0041/0064/0067) can't find a spec that
  legitimately exists elsewhere because the target repo has multiple worktrees on different
  branches.

Scope now narrowed accordingly: this idea is about that one real, narrow case (multi-worktree
target repos), not the broader "sweep reports missing" symptom, which had other causes now
already fixed by hand. The technical design from the first explore pass (git-plumbing lookup
across worktrees, preferring `git log --all`/`git show` over directory-scanning siblings
because it survives a worktree being deleted later) still stands and is still worth building
-- it's just a smaller, more precisely-scoped fix than originally framed, and "wholly separate
repo clones" stays an explicit Non-goal per the original framing.
** Open questions
*** RESOLVED Worktree discovery: shell out to git worktree list --porcelain against outbox_targets[project].repo_path (assumes it's itself a worktree/repo root wt can run git in), or read .git-file-based worktree metadata directly? Any risk running git as a subprocess from wt (perf, error handling on a non-repo path, Windows/exotic setups)?
Resolved: shell out to git worktree list --porcelain, run with cwd=repo_path (or -C repo_path). Verified the failure mode is clean: against a non-repo path it exits 128 with 'fatal: not a git repository...' on stderr -- easy to catch (non-zero returncode) and just skip worktree-awareness silently, falling back to today's single-path behavior. No .git-file parsing needed; the porcelain output is a stable, documented git interface. Perf: one subprocess call per sweep/pull_status invocation (not per idea), negligible next to sweep's own per-idea work.
*** RESOLVED Search strategy once worktrees are enumerated: check each sibling worktree's on-disk docs/specs/<file> path (only finds it if that worktree happens to still be checked out and not pruned), or use git plumbing (git show <any-branch>:<path> / git log --all -- <path>) against the shared object store, which works even if the authxxing worktree has since been deleted? The Log's own git log --all check suggests the plumbing approach is strictly more robust.
Resolved: prefer git plumbing (git log --all -- <relpath> to find touching commits, then git show <commit>:<relpath> for content) over scanning sibling worktree directories. Confirmed both approaches would have found EXAMPLE-0026 here, but plumbing is strictly more robust -- it survives the authxxing worktree being deleted/pruned later (git worktree remove is routine cleanup after a branch merges), since it reads the shared object store directly rather than depending on some worktree still being checked out to the right branch on disk. Directory-scanning sibling worktrees is simpler code but a strictly weaker fallback; plumbing should be the primary strategy, with a directory scan as a cheap first check (skip the git subprocess entirely when the naive repo_path lookup already succeeds).
*** RESOLVED If found via git history/another worktree but not in the configured repo_path's working tree, what does wt actually do with it -- just report an accurate status (unblocks sweep/pull_status), or also suggest/offer to materialize a copy at the expected repo_path location so future lookups are cheap again?
Resolved (leaning): report accurate status only for now -- unblock sweep/pull_status/pull_clock so they stop crying 'missing' for specs that actually exist, without also writing a copy back to the configured repo_path. Materializing a copy is tempting but adds a new write path with its own non-clobber/conflict questions (SPEC-0016's whole division-of-labor concern) for a problem that's really about **reading** status correctly. Revisit as a follow-up if 'the file isn't where repo_path says' turns out to cause its own confusion in practice.
*** RESOLVED Scope for 'separate repo copies' (not a worktree of the same repo): explicitly a Non-goal for auto-discovery (per the human's own framing), but should there be a manual escape hatch -- e.g. an optional outbox_targets[project].extra_search_paths list -- or leave it fully unsolved for now?
Resolved: Non-goal for auto-discovery, confirmed by the human's own framing. A manual escape hatch (e.g. outbox_targets[project].extra_search_paths: [...]) is cheap to add alongside the worktree fix and directly serves the 'separate clone on this machine' case without needing any discovery heuristics -- worth including in the same child, not a fully separate effort, since it is likely near-zero extra code once a 'try N candidate paths' resolution shape already exists for worktrees.
*** RESOLVED Which callers need this fix: just wt spec sweep/pull_status (status-mirroring reads), or also pull_clock and anything else in export.py that resolves _portable_dest_path -- should the worktree-aware resolution live as one shared helper all of them call?
Resolved: exactly 2 callers of _portable_dest_path in src/wt/export.py -- pull_status (line 220) and pull_clock (line 265). Both should go through one shared worktree/plumbing-aware resolution helper (e.g. _resolve_portable_spec(cfg, source_path, fm, to=) returning the found path or raising the same ValueError as today), so sweep (which calls both per idea) gets the fix for free rather than needing its own logic.
** Log
*** [2026-08-06 Thu 20:18]
Explore pass: verified 'git worktree list --porcelain' cleanly fails (exit 128, clear stderr) against a non-repo path -- safe to shell out and fall back silently. Found exactly 2 call sites needing the fix (export.py: pull_status:220, pull_clock:265), both via _portable_dest_path -- one shared helper covers sweep too. Confirmed via IDEA-212/EXAMPLE-0026's real case that git log --all -- <path> finds the file from the main worktree's own .git even though it only exists checked-out in a sibling worktree (example-ats-1, branch user/EXAMPLE-0026-stream-observer) -- git plumbing against the shared object store is the robust primary strategy; a sibling-worktree directory scan is a cheap but weaker fallback (only works while that worktree still exists on disk). All 5 open questions resolved.
*** [2026-08-06 Thu 20:36]
Correction: tested all ~20 examples from the original wt spec sweep output, not just IDEA-212/EXAMPLE-0026. Found the dominant pattern (18 of 20) was NOT worktree-scatter -- it was deliberate PR spec-stripping (a team convention) plus a few specs that had simply never been exported. Both fixed by hand this session (wt spec export --to for each, non-destructively, as local uncommitted files) -- wt spec sweep is now fully clean. Only EXAMPLE-0026 was a genuine worktree case, confirming the original design direction but at much narrower scope than first framed. Retitled/reframed accordingly before promotion.

## Goals / Non-goals

**Goals**
- `pull_status`/`pull_clock`/`sweep` find a portable spec that exists in a sibling git
  worktree of `outbox_targets[project].repo_path` (same repo, different working directory,
  different checked-out branch), not just at the one static configured path.
- Resolution degrades gracefully to today's exact behavior when `repo_path` isn't a git repo,
  has no other worktrees, or `git` isn't available — no new failure mode for the common case.
- A manual escape hatch (`outbox_targets[project].extra_search_paths`) for the "separate
  clone on this machine" case, since auto-discovery of that is explicitly out of scope.

**Non-goals**
- Auto-discovering a wholly separate clone of the same repo (different `.git`, no shared
  object store) — confirmed Non-goal (IDEA-235 Q4); `extra_search_paths` is the only lever.
- Writing/materializing a found file back into the configured `repo_path` — this is a read-path
  fix only (IDEA-235 Q3).
- Any change to `wt spec export`'s file-drop behavior — this spec only touches how an
  *already-exported* spec's current location is found for status/clock mirroring.

## Decision

Add `export._resolve_portable_spec(cfg, source_path, fm, to=None) -> Path`, replacing direct
calls to `_portable_dest_path` in `pull_status`/`pull_clock`. It first tries today's exact
resolution (`_portable_dest_path`); if that path doesn't exist, it tries each path in
`outbox_targets[project].extra_search_paths` (if configured), then falls back to a
git-plumbing search (`git log --all -- <relpath>` + `git show <commit>:<relpath>`) run against
`repo_path` if it's a git repository. The first hit wins; if nothing is found anywhere, the
original `ValueError` is raised unchanged.

## Design

**`src/wt/export.py`**:

```python
def _git_plumbing_lookup(repo_path: Path, relpath: str) -> str | None:
    """Return file content at `relpath` from the most recent commit that touched it, anywhere
    in `repo_path`'s repo (any branch/worktree, including ones since deleted) — or None if
    `repo_path` isn't a git repo, git isn't available, or no commit ever touched that path."""
    try:
        log = subprocess.run(
            ["git", "-C", str(repo_path), "log", "--all", "--format=%H", "-1", "--", relpath],
            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    commit = log.stdout.strip()
    if log.returncode != 0 or not commit:
        return None
    show = subprocess.run(["git", "-C", str(repo_path), "show", f"{commit}:{relpath}"],
                          capture_output=True, text=True, timeout=5)
    return show.stdout if show.returncode == 0 else None


def _resolve_portable_spec(cfg, source_path, fm, *, to=None) -> Path:
    """Find where an already-exported portable spec actually lives: the configured/frozen
    path first (unchanged fast path), then extra_search_paths, then a git-plumbing search of
    repo_path's history (SPEC-0130) — covering a spec that only exists in a sibling worktree
    on an unmerged branch. Writes a found-elsewhere copy to a tempfile-backed Path so callers
    (pull_status/pull_clock) can keep reading it as a normal file, unchanged."""
    primary = _portable_dest_path(cfg, source_path, fm, to=to)
    if primary.exists():
        return primary
    project = fm.get("target_project")
    target_cfg = (cfg.get("outbox_targets") or {}).get(project, {})
    relpath = None
    for extra in target_cfg.get("extra_search_paths", []):
        candidate = Path(extra).expanduser() / primary.name
        if candidate.exists():
            return candidate
    repo_path = target_cfg.get("repo_path")
    if repo_path:
        spec_dir = target_cfg.get("spec_dir", "docs/specs")
        relpath = f"{spec_dir}/{primary.name}"
        content = _git_plumbing_lookup(Path(repo_path).expanduser(), relpath)
        if content is not None:
            return _write_temp_copy(content, primary.name)
    return primary   # unchanged: callers raise their own "not found" ValueError on this path
```

- `pull_status`/`pull_clock` (`export.py:220`, `:265`) call `_resolve_portable_spec` instead of
  `_portable_dest_path` directly; no other change to their logic — they already just read
  `dest_path` after resolving it.
- `_write_temp_copy` is a small helper writing `content` to a `tempfile`-backed path (cleaned
  up isn't necessary — these are read-once, short-lived, OS-managed tmp files) so the rest of
  `pull_status`/`pull_clock` keeps working with a plain `Path.read_text()`/`.exists()` contract,
  unaware whether the source was on-disk or reconstructed from git history.
- `extra_search_paths` is a new, optional, freeform list under `outbox_targets[project]` —
  no `config.py` change needed (same shallow-merge mechanism as `sheet`, SPEC-0124).

## Alternatives considered

- **Scan sibling worktree directories via `git worktree list` instead of git plumbing** —
  rejected as the *primary* strategy (IDEA-235 Q2): weaker, since it only finds a file while
  the authxxing worktree still exists on disk. Not implemented at all, since plumbing already
  subsumes it (a checked-out worktree's content is also reachable via `git log --all` on that
  same branch) — no need for two mechanisms doing overlapping work.
- **Materialize the found file back into `repo_path`** — rejected (Non-goals); read-path fix
  only.
- **Search for the file by content hash instead of path** — rejected as unnecessary
  complexity; the relpath is already known from `_portable_dest_path`'s own naming convention.

## Acceptance criteria

- [x] `pull_status`/`pull_clock`/`sweep` on a spec that exists only via `git log --all` in
      `repo_path`'s history (not at the configured path, not checked out anywhere) succeed
      instead of raising "portable spec not found"
      (`test_pull_status_falls_back_to_git_history_when_missing_at_configured_path`,
      `test_pull_clock_falls_back_to_git_history`).
- [x] The exact EXAMPLE-0026 scenario (spec content only in a sibling worktree's checked-out
      branch) resolves correctly via the same git-history path — verified live: removed the
      manually-dropped local copy and `wt spec sweep` found it via plumbing with no manual
      export needed.
- [x] `outbox_targets[project].extra_search_paths` is checked before falling back to git
      plumbing, and a hit there is used verbatim (`test_pull_status_extra_search_paths_hit_before_git`).
- [x] When `repo_path` isn't a git repository (or `git` errors/times out), resolution falls
      back to exactly today's behavior — `test_git_plumbing_lookup_returns_none_for_non_git_path`.
- [x] When the spec truly doesn't exist anywhere (never exported), the original `ValueError`
      message is unchanged, byte-for-byte —
      `test_pull_status_raises_original_error_when_nowhere_to_be_found`.

## Test plan

- **Automated tests:** `tests/test_export.py` gained 6 new cases: a fixture git repo (real
  `git init`/`commit` via `subprocess` in a tmp dir) with a spec committed then removed from
  the working tree, asserting `pull_status`/`pull_clock` succeed via the git-history
  fallback; `extra_search_paths` hit (no git needed); non-git `repo_path` and no-history-
  anywhere both asserting the original `ValueError` message is unchanged; a direct unit test
  of `_git_plumbing_lookup` against a non-repo path.
- **Manual verification:** performed live against the real case that motivated this spec —
  removed the manually-dropped local copy of `~/work/example-repo-ats/docs/specs/EXAMPLE-0026-...md`
  (the workaround applied earlier in the session) and re-ran `wt spec sweep`: it found the
  spec via git plumbing from the sibling `example-ats-1` worktree's branch history with no
  manual export needed, confirming the fix works against the exact scenario that started this
  investigation.
- **Regression guard:** `uv run pytest` green (1109 passed); existing `tests/test_export.py`
  cases (the fast, already-exists path) unaffected — `_resolve_portable_spec`'s first branch
  is exactly the old `_portable_dest_path` call.

## Rollout / migration

Pure addition: new function + 2 call-site substitutions in `export.py`; `extra_search_paths`
is optional config, defaulting to absent (no behavior change for any project that doesn't set
it). No data migration.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — resolved on IDEA-235 before accept)

## What shipped / deviations

Implemented as designed: `_git_plumbing_lookup`, `_write_temp_copy`, `_resolve_portable_spec`
in `src/wt/export.py`; `pull_status`/`pull_clock` both now call `_resolve_portable_spec`
instead of `_portable_dest_path` directly. No deviations. `extra_search_paths` is a new,
optional, freeform config key under `outbox_targets[project]` — no `config.py` change needed
(same shallow-merge as every other per-project config addition this session).
