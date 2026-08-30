---
id: SPEC-0079
title: "specs_dir defaults to cwd/docs/specs, so any test with an incomplete"
status: done
owner: user
created: 2026-07-27
source_idea: IDEA-100
updated: 2026-07-27
milestone: "M0: process"
tags: [infra, tooling, specs]
# depends_on: []
# supersedes: []
# superseded_by: SPEC-NNNN
---

## Context

Promoted from idea `IDEA-100` (specs_dir defaults to cwd/docs/specs, so any test with an incomplete config fixture silently writes to the live repo instead of tmp_path).

  :PROPERTIES:
  :ID: IDEA-100
  :CREATED: [2026-07-27 Mon 20:38]
  :UPDATED: [2026-07-27 Mon 20:56]
  :PROJECT: Meta-Tools
  :KIND: bug
  :END:
** Summary
`_specs_dir(cfg)` (`src/wt/specs.py:46`) is `Path(cfg.get("specs_dir") or (Path.cwd() / "docs" / "specs"))`. The fallback is **cwd-relative** and `pytest` runs from the repo root, so a test whose config fixture omits `specs_dir` resolves spec lookups against the **live** `docs/specs` instead of its `tmp_path` sandbox. Reads return the wrong data; **writes hit tracked files**.

**Observed, not theorised.** While implementing SPEC-0078 a first version of `tests/test_reconcile.py` omitted `specs_dir`. The run wrote a bogus `source_idea` into `docs/specs/0001-package-refactor-and-xdg-layout.md` and `0003-epic-and-subspec-model.md` and reformatted both frontmatter blocks. Nothing in the test output pointed at it — the tests reported ordinary assertion failures; it surfaced only because those two files then appeared as **new** entries in `spec_lint.py --check-source-ideas`. Reverted with `git checkout`.

──────── What exploration established ────────

**Latent, not active.** Measured by instrumenting `_specs_dir` to log every fallback and running the full suite: **zero** hits across 588 tests. The 16 fixtures lacking `specs_dir` never reach spec resolution, because their ideas carry no `:SPEC:` and `next_step_for_idea` returns early (`workflow.py:147`). The trap springs only when a test omits the key **and** touches spec resolution. (This corrects the framing at capture time, which mistakenly equated "fixture omits the key" with "test reads live specs".)

**Precisely one offender.** Audit of every cwd-relative construct in `src/wt/` + `tools/`: only `specs.py:47` uses the silent `cfg.get(...) or <ambient>` shape. `outbox_dir` (`specs.py:305`) subscripts `cfg["data_dir"]` and so raises `KeyError` when unset; `config_dir`/`data_dir` are filled by `load_config`. The defect is the **silent .get-with-ambient-fallback pattern**, not ambient defaults generally — so there is no wider audit to do.

**The dangerous writer is `promote_idea`, not the one that bit us.** Of the eleven `_specs_dir` consumers (`workflow.py:43,79`; `specs.py:122,227,276,367,416`; `completion.py:209,232`; `report.py:125`) two write. `_write_source_idea` annotates an existing file. `promote_idea` (`specs.py:122-147`) calls `next_spec_number(specs_dir)` then `spec_path.write_text(text)` — a test invoking it without `specs_dir` would **create a new tracked `docs/specs/NNNN-**.md` in the live repo*, numbered off the real corpus and consuming the next real spec id. Worse than what actually happened.

**No `tests/conftest.py` exists**, so the "guard" direction is net-new infrastructure. 16 test files set `specs_dir`, 16 do not.

──────── Where this points ────────
Two independent levers, and they are not alternatives:
- **Remove the trap:** make `specs_dir` required (raise on absence) or default to something non-ambient (git root / package root). Cheap, targeted, kills this instance.
- **Catch the class:** an autouse `conftest.py` fixture that fails any test whose writes land outside `tmp_path`. Costlier, but this specific escape went unnoticed through a full test run and was caught by luck — a write to a file no checker inspects would not have been caught at all.
** Open questions
*** OPEN Should =specs_dir= become *required* (raise on absence) or keep a default that is simply not cwd-relative (git root / installed package root)? Raising is safest but touches every caller and every fixture.
*** OPEN Is the real fix a guard rather than a default — e.g. an autouse conftest fixture that fails any test whose writes land outside =tmp_path=? That catches this whole *class* of escape, not just =specs_dir=.
*** RESOLVED How many existing test fixtures omit =specs_dir= and are therefore reading the live =docs/specs= today (passing for the wrong reason)?
*** RESOLVED Do other cwd-relative or ambient defaults exist with the same shape (=outbox_dir=, =data_dir=, =org_files=)? Worth auditing together rather than patching one.
*** OPEN Should ~_write_source_idea~-style writers refuse to touch a path outside a configured root as a belt-and-braces measure, independent of how the default is fixed?
*** OPEN Given ~promote_idea~ can mint a real spec file, should the fix be ordered — required-=specs_dir= first (small, immediate) and the tmp_path write-guard later as its own piece — or is shipping only the former leaving the class of bug open?
** Log
*** [2026-07-27 Mon 20:38]
Discovered during SPEC-0078 implementation (`wt spec reconcile`), reported to the human, who asked for it to be filed as a bug rather than left as a footnote in that specs Rollout section.

Concrete trace: `tests/test_reconcile.py` built its `cfg` without `specs_dir`; `_specs_dir` fell back to `Path.cwd()/docs/specs`; `_write_source_idea` resolved SPEC-0001/SPEC-0003 to the real tracked files and wrote to them. Reverted via `git checkout`; `git status` confirmed no other tracked file was affected. The fixture now sets `specs_dir` explicitly (with a comment saying why), and SPEC-0078 gained a regression test asserting the back-link write changes exactly one line — but **neither** of those fixes the underlying default.

Note the near-miss: the two damaged files were only noticed because they surfaced as new `--check-source-ideas` entries. A test touching a spec file that no checker inspects would have gone unnoticed entirely.
*** [2026-07-27 Mon 20:55]
Explored `/home/user/work/tools/work-tracking` (research root, internal). Three measurements, one of which **corrects a claim made when this idea was filed**.

**1 — Correction: no test currently hits the fallback. The bug is latent, not active.**
When filing this I said 16 test files "are resolving against the live `docs/specs` right now". That was wrong — it counted fixtures missing the key, not code paths reached. Measured properly by patching `_specs_dir` to append `PYTEST_CURRENT_TEST` to a log on every fallback, verifying the patch was in place, running the full suite (588 passed), then restoring: **zero** fallback calls. The 16 fixtures omit `specs_dir` but never reach spec resolution, because their ideas carry no `:SPEC:` and `next_step_for_idea` returns early (`src/wt/workflow.py:147`) before `_resolve_spec_path`. The escape fires only when a test **both** omits =specs_dir** **and* exercises spec resolution — which is exactly what the new SPEC-0078 test did.

**2 — `specs_dir` is the only silent ambient default; the others fail loudly.**
Audited every cwd-relative construct in `src/wt/` and `tools/`. Only `specs.py:47` uses the `cfg.get(...) or <ambient>` shape. The neighbours are safe by accident of style: `outbox_dir` (`specs.py:305`) derives from `cfg["data_dir"]` — a **subscript**, so a fixture omitting it raises `KeyError` immediately; `config_dir` / `data_dir` are populated by `load_config` from XDG paths. So the defect is precise: **silent `.get` fallback to an ambient location**, not "ambient defaults" in general. Narrows question 4 considerably — there is nothing else to audit.

**3 — The worst writer is not the one that bit us.**
Inventory of `_specs_dir` consumers: `workflow.py:43,79`, `specs.py:122,227,276,367,416`, `completion.py:209,232`, `report.py:125`. Most read. Two write:
- `_write_source_idea` (SPEC-0078) — annotates an existing spec. This is what damaged 0001/0003.
- `promote_idea` (`specs.py:122-147`) — computes `next_spec_number(specs_dir)` and does `spec_path.write_text(text)`. A test calling it without `specs_dir` would **mint a brand-new `docs/specs/NNNN-**.md` into the live repo*, numbered off the real corpus. Strictly worse than an annotation: a new tracked file, plausible-looking, and it would silently consume the next real spec number.

**4 — There is no `tests/conftest.py` at all.**
So the guard option (question 2) has no existing home; it would be a new file. Cheap, but worth knowing it is net-new infrastructure rather than an edit. 16 of the test files do set `specs_dir`, 16 do not — the split is roughly even, so a conftest autouse default would change behaviour for half the suite.

## Goals / Non-goals

**Goals**

- `_specs_dir` never silently resolves to an ambient location. A caller that has not said where
  the specs live gets an error, not a guess.
- Real CLI use is unaffected: `wt` keeps working with no `specs_dir` in `config.yaml`.
- Every test fixture states its specs dir explicitly, so no test can reach the live repo.

**Non-goals**

- Not adding the `tests/conftest.py` write-guard that fails any test writing outside `tmp_path`.
  That catches the whole class of sandbox escape and is worth doing, but it is net-new test
  infrastructure and independent of this fix — filed separately.
- Not touching `outbox_dir` / `data_dir` / `config_dir`. The audit found they already fail loudly
  (`cfg["data_dir"]` is a subscript, so an unset fixture raises `KeyError`); `specs_dir` is the
  only silent-fallback offender.
- No change to what `wt` resolves at runtime for a real user.

## Decision

`_specs_dir(cfg)` stops falling back to `Path.cwd() / "docs" / "specs"`. Resolution order
becomes:

1. `cfg["specs_dir"]` when set — unchanged, and what every test will now use.
2. otherwise the **repo root discovered from this module's own location**
   (`Path(__file__).resolve().parents[2] / "docs" / "specs"`), which is where wt's specs actually
   live for real CLI use.
3. if that directory does not exist, raise `ValueError` naming `specs_dir`.

The difference that matters: the default is anchored to *the installed package*, not to wherever
the process happens to be running. A test running from the repo root no longer silently inherits
the live corpus by coincidence of cwd — it gets an explicit path that a fixture is expected to
override, and a clear error if neither is usable.

The 16 test fixtures that omit `specs_dir` get it, pointing at `tmp_path`.

## Design

### `_specs_dir` (`src/wt/specs.py:46`)

```python
def _specs_dir(cfg):
    """Where internal SPEC-NNNN files live. `cfg['specs_dir']` wins; otherwise wt's own
    docs/specs, located from this module rather than from the cwd (SPEC-0079)."""
```

`Path(__file__).resolve().parents[2]` is `<repo>/` from `<repo>/src/wt/specs.py`. When wt is
installed rather than run from a checkout that path will not contain `docs/specs`, and the
`ValueError` tells the caller to set `specs_dir` — which is the correct outcome, since an
installed wt has no internal spec corpus of its own.

*(As-built: this also fixes a user-facing bug nobody had filed.* Under the cwd default, running
`wt` from anywhere other than the repo root resolved `<cwd>/docs/specs`, which does not exist —
so `wt hub --json` silently reported **zero** internal specs and `next_step_for_idea` reported
every linked spec as missing. Verified after the change: from `/tmp`, `wt hub --json` resolves
the internal specs correctly. The fallback was not just unsafe in tests, it was wrong in normal
use.)

Callers are unchanged: all eleven consumers (`workflow.py:43,79`; `specs.py:122,227,276,367,416`;
`completion.py:209,232`; `report.py:125`) keep calling `_specs_dir(cfg)`.

### Why not simply require `specs_dir`

Raising whenever the key is absent is the tighter rule, but it breaks real CLI use: `wt spec new`
run from a checkout has no `specs_dir` in `config.yaml` today and is expected to find
`docs/specs`. Requiring the key would force every user to configure something wt can determine
for itself. Anchoring the default to the package keeps the ergonomics and removes the ambiguity,
which is the actual defect — the old behaviour was not "has a default", it was "has a default
that changes with your working directory".

### Test fixtures

The 16 files whose `cfg` omits `specs_dir` gain `"specs_dir": str(tmp_path / "specs")` (created
in the fixture). This is what makes the escape structurally impossible for them rather than
merely unreached: today they are safe only because their ideas happen to carry no `:SPEC:`.

## Alternatives considered

- **Require `specs_dir`, raise when absent** — tightest, and rejected: it breaks `wt` for a user
  running from a checkout with no `specs_dir` configured, to fix a problem that only exists in
  tests.
- **Keep the cwd default, fix only the fixtures** — leaves the trap armed for the next test.
- **`conftest.py` autouse write-guard** — catches this *and* every other sandbox escape, and is
  the stronger long-term answer. Deferred deliberately: it is new infrastructure, would change
  behaviour for half the suite, and this fix should not wait on it.
- **Git-root discovery (walk up for `.git`)** — works in a checkout, fails for an installed
  package, and adds filesystem walking for no gain over `__file__`.

## Acceptance criteria

- [x] `_specs_dir({})` does not depend on the current working directory: called from a different
      cwd it returns the same path.
- [x] `_specs_dir({"specs_dir": X})` returns `X` unchanged.
- [x] With no `specs_dir` and no discoverable `docs/specs`, `_specs_dir` raises `ValueError`
      naming `specs_dir`.
- [x] Running the real CLI from a checkout still resolves wt's own `docs/specs` with no
      `specs_dir` configured (`wt spec reconcile`, `wt hub --json` work unchanged).
- [x] No test fixture in `tests/` omits `specs_dir`.
- [x] Instrumenting `_specs_dir` and running the full suite shows zero resolutions to the live
      `docs/specs`.
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_specs_dir.py` (7 tests):

- `test_explicit_specs_dir_wins` — the configured path is returned verbatim.
- `test_default_is_independent_of_cwd` — resolve once, `os.chdir(tmp_path)`, resolve again;
  identical. This is the actual bug, so it is asserted directly.
- `test_missing_docs_specs_raises` — monkeypatch the package anchor to a directory with no
  `docs/specs`; assert `ValueError` mentioning `specs_dir`.
- `test_no_test_fixture_omits_specs_dir` — scan `tests/*.py` for config-dict literals containing
  `org_ideas_file` and assert each also sets `specs_dir`. A meta-test, because the failure mode
  is a *new* fixture forgetting the key, which no runtime assertion in an existing test catches.
- `test_specs_dir_has_no_cwd_fallback_in_source` — assert the resolver's own body contains no
  `cwd()`/`getcwd`. Re-introducing the fallback would silently re-arm the trap while every other
  test kept passing, so the fix itself needs a guard.
- `test_default_is_wts_own_specs_dir`, `test_empty_string_specs_dir_falls_back_not_crashes` —
  the default is the package's `docs/specs`; an empty-string config value behaves as unset
  rather than resolving to `.`.

**Manual verification**

1. `uv run wt spec reconcile` from the repo root — resolves specs as before.
2. `cd /tmp && uv run --project <repo> wt hub --json` — internal specs still resolve, proving the
   default no longer depends on cwd.

**Regression guard**

Full `uv run pytest`; `tests/test_specs.py`, `tests/test_export.py`, `tests/test_reconcile.py`
and `tests/test_workflow.py` all exercise spec resolution and pass untouched. Re-ran the
`_specs_dir` instrumentation from the IDEA-100 exploration after the change: across 595 tests
the package default is reached by **6 calls, all from `tests/test_specs_dir.py`**, which asserts
that behaviour deliberately. Every other test now supplies its own `specs_dir`.

## Clock Log

Clocked on IDEA-100 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

Single commit: the resolver change plus the fixtures. No data migration. **Done:** 9 fixture
files gained `specs_dir` (8 by pattern, `tests/test_join.py` by hand — its config literal is
laid out differently); the other test files already set it. Suite 588 → 595.

One user-visible change, an improvement rather than a break: `wt` invoked from outside the repo
now finds wt's own internal specs instead of silently finding none.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Required vs non-ambient default* → non-ambient default anchored to the package; requiring the
  key would break real CLI use.
- *Guard as the real fix* → complementary, not a substitute; filed separately so this does not
  wait on it.
- *Wider ambient-default audit* → no other offenders; `specs_dir` is the only silent `.get`
  fallback.
- *Ordering* → this first (small, immediate); the write-guard as its own piece.
