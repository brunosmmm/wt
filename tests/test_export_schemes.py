"""Pluggable export schemes (SPEC-0016): registry lookup/available(); wt-native render still
matches SPEC-0015's expected shape; REMOVED renders a feature spec into a task-spec seed
and an epic into a task-spec + project-plan.md deliverable fragment (matching REMOVED's
task-spec-template.md / REMOVED conventions); a manifest-defined TemplateScheme
renders a simple remap with no Python; scheme validation blocks a spec missing a required
field before any file is written; non-clobbering (owned files + project-plan splice).

Everything here uses a TMP outbox dir + TMP --to target (never docs/outbox/ or a real repo).
"""
import importlib.util
import pathlib

import pytest
from zoneinfo import ZoneInfo

from wt import export as E
from wt import export_schemes as ES
from wt import specs as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
REAL_SPECS = ROOT / "docs" / "specs"
LINT = ROOT / "tools" / "spec_lint.py"


def _linter():
    spec = importlib.util.spec_from_file_location("spec_lint_schemes", LINT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cfg(tmp_path, outbox_targets=None):
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    import shutil
    shutil.copy(REAL_SPECS / "TEMPLATE.md", specs_dir / "TEMPLATE.md")
    outbox = tmp_path / "outbox"
    return {"specs_dir": str(specs_dir), "outbox_dir": str(outbox),
            "outbox_targets": outbox_targets or {}, "timezone": "America/New_York",
            "_tz": ZoneInfo("America/New_York")}


def _scaffold(cfg, project, title, **extra_fm):
    path, outbound_id = S.scaffold_outbound(cfg, project, title=title)
    if extra_fm:
        text = path.read_text()
        fm, body = text.split("---\n", 2)[1:]
        lines = fm.rstrip("\n").splitlines()
        for k, v in extra_fm.items():
            lines.append(f"{k}: {v}")
        text = "---\n" + "\n".join(lines) + "\n---\n" + body
        path.write_text(text)
    return path, outbound_id


def _fill_acceptance_and_test_plan(path, acceptance_items, test_plan_lines):
    text = path.read_text()
    accept_block = "\n".join(f"- [ ] {a}" for a in acceptance_items)
    text = text.replace(
        "## Acceptance criteria\n\n<What must be TRUE for this to be correct. Each item must "
        "be objectively checkable.>\n\n- [ ] …\n- [ ] …",
        f"## Acceptance criteria\n\n{accept_block}")
    tp_block = "\n".join(test_plan_lines)
    text = text.replace(
        "## Test plan\n\n<HOW we prove the acceptance criteria. Required for feature/behavior "
        "specs; for a pure\npolicy/doc spec write \"N/A — <reason>\". Cover:>\n\n"
        "- **Automated tests:** which tests, where (`tests/…`), what they assert; fixtures "
        "needed.\n- **Manual verification:** exact commands/steps to run and the expected "
        "result.\n- **Regression guard:** how we confirm existing behavior is unchanged.",
        f"## Test plan\n\n{tp_block}")
    path.write_text(text)
    return path


# ---- registry ----------------------------------------------------------------------

def test_registry_available_includes_builtins():
    names = {s.name for s in ES.available()}
    assert "wt-native" in names
    assert "REMOVED" in names
    assert "plain-md" in names


def test_registry_get_unknown_raises():
    with pytest.raises(ValueError, match="unknown export scheme"):
        ES.get("nope")


def test_registry_get_returns_registered_scheme():
    assert ES.get("wt-native").name == "wt-native"


# ---- wt-native (regression guard against SPEC-0015 shape) ---------------------------

def test_wt_native_is_default_and_matches_spec0015_shape(tmp_path):
    cfg = _cfg(tmp_path)
    src_path, outbound_id = _scaffold(cfg, "acme", "Adversarial reviewer")
    target = tmp_path / "target-repo"

    dest_spec, dest_contract = E.export_spec(cfg, outbound_id, to=str(target))

    assert dest_spec == target / "docs" / "specs" / src_path.name
    assert dest_spec.exists() and dest_contract.exists()
    text = dest_spec.read_text()
    assert "source_outbound_id" in text and "source_content_hash" in text
    assert "target_project" not in text

    # explicit --scheme wt-native reproduces the same output byte-for-byte
    target2 = tmp_path / "target-repo-explicit"
    dest_spec2, dest_contract2 = E.export_spec(cfg, outbound_id, scheme="wt-native",
                                               to=str(target2))
    assert dest_spec2.read_text() == text
    assert dest_contract2.read_text() == dest_contract.read_text()


def test_wt_native_validate_blocks_missing_context(tmp_path):
    cfg = _cfg(tmp_path)
    path, outbound_id = _scaffold(cfg, "acme", "No context")
    text = path.read_text().replace(
        "## Context\n\n<Why are we doing this? What exists today? What's the problem or "
        "opportunity?>", "## Context\n\n")
    path.write_text(text)

    with pytest.raises(ValueError, match="fails validation"):
        E.export_spec(cfg, outbound_id, to=str(tmp_path / "target"))
    assert not (tmp_path / "target").exists()


# ---- REMOVED: feature spec -> one task-spec seed --------------------------------

def _feature_fixture(cfg, tmp_path, task_base="1.2"):
    path, outbound_id = _scaffold(cfg, "sdlcbundle-REMOVED", "Adversarial reviewer",
                                  scope_paths="src/review/")
    _fill_acceptance_and_test_plan(
        path,
        ["I can review a session for contradictions", "Reviewer flags contradictions", "Reviewer output is deterministic"],
        ["- **Automated tests:** `uv run pytest tests/test_review.py`",
         "- **Manual verification:** run `wt review --fix` and confirm no crash.",
         "- **Regression guard:** `uv run pytest` full suite green."])
    return path, outbound_id


def test_REMOVED_feature_renders_task_spec_seed(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _feature_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"

    written = E.export_spec(cfg, outbound_id, to=str(target))
    assert isinstance(written, list)
    assert len(written) == 1
    task_path = written[0]
    assert task_path == target / "specs" / "tasks" / "1.2.1-adversarial-reviewer.md"
    assert task_path.exists()

    text = task_path.read_text()
    # task-spec-template.md shape
    for heading in ["# Task Spec: 1.2.1 — Adversarial reviewer", "## Context",
                    "## Requirements", "### Functional Requirements",
                    "### Non-Functional Requirements", "## Technical Approach",
                    "## Acceptance Criteria", "## Verification Steps",
                    "### Build Verification", "### Unit Test Verification",
                    "### Integration Test Verification", "### Manual Verification",
                    "## Dependencies", "## Out of Scope"]:
        assert heading in text, heading

    # binary checkboxes
    assert "- [ ] Reviewer flags contradictions" in text
    assert "- [ ] Reviewer output is deterministic" in text
    # fenced command block lifted from the Automated tests bullet
    assert "```bash\nuv run pytest tests/test_review.py\n```" in text
    # PM markers where wt lacks data
    assert "<!-- PM:" in text
    # no architecture/style doc content, no wt consumption contract
    assert "consumption" not in text.lower()


def test_REMOVED_no_project_plan_for_a_plain_feature(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _feature_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"

    written = E.export_spec(cfg, outbound_id, to=str(target))
    assert not (target / "project-plan.md").exists()
    assert all(p.name != "project-plan.md" for p in written)


# ---- REMOVED: epic -> task-spec(s) + project-plan.md fragment -------------------

def _epic_fixture(cfg, tmp_path):
    path, outbound_id = S.scaffold_outbound(cfg, "sdlcbundle-REMOVED", title="Review platform")
    text = path.read_text()
    text = text.replace("id: " + outbound_id, "id: " + outbound_id + "\nkind: epic")
    text = text.replace(
        "## Acceptance criteria\n\n<What must be TRUE for this to be correct. Each item must "
        "be objectively checkable.>\n\n- [ ] …\n- [ ] …",
        "## Acceptance criteria\n\n- [ ] I can use the reviewer platform end to end\n"
        "- [ ] Reviewer platform ships end to end")
    text = text.replace(
        "## Test plan\n\n<HOW we prove the acceptance criteria. Required for feature/behavior "
        "specs; for a pure\npolicy/doc spec write \"N/A — <reason>\". Cover:>\n\n"
        "- **Automated tests:** which tests, where (`tests/…`), what they assert; fixtures "
        "needed.\n- **Manual verification:** exact commands/steps to run and the expected "
        "result.\n- **Regression guard:** how we confirm existing behavior is unchanged.",
        "## Test plan\n\n- **Automated tests:** `uv run pytest tests/test_platform.py`")
    text += ("\n## Breakdown / sub-specs\n\n"
            "- Adversarial reviewer\n- Reviewer CLI wiring\n")
    path.write_text(text)
    return path, outbound_id


def test_REMOVED_epic_renders_tasks_and_project_plan(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _epic_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"

    written = E.export_spec(cfg, outbound_id, to=str(target))
    names = sorted(p.name for p in written)
    assert names == ["1.2.1-adversarial-reviewer.md", "1.2.2-reviewer-cli-wiring.md",
                     "project-plan.md"]

    plan = (target / "specs" / "project-plan.md").read_text()
    assert "### Deliverable 1.2" in plan
    assert "#### 1.2.1 — Adversarial reviewer" in plan
    assert "#### 1.2.2 — Reviewer CLI wiring" in plan
    assert "**Outcome / Deliverable:**" in plan
    assert "**Do:**" in plan and "**Test bar:**" in plan


def test_REMOVED_project_plan_splice_preserves_other_content(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _epic_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"
    (target / "specs").mkdir(parents=True)
    existing = ("# Project plan\n\n"
               "### Deliverable 1.1\n\n**Objective:** unrelated deliverable\n\n"
               "#### 1.1.1 — Something else\n\n**Outcome / Deliverable:** unrelated\n")
    (target / "specs" / "project-plan.md").write_text(existing)

    E.export_spec(cfg, outbound_id, to=str(target))
    plan = (target / "specs" / "project-plan.md").read_text()
    assert "### Deliverable 1.1" in plan
    assert "unrelated deliverable" in plan
    assert "### Deliverable 1.2" in plan
    assert "#### 1.2.1 — Adversarial reviewer" in plan


def test_REMOVED_never_emits_architecture_or_style_docs(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _epic_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"
    written = E.export_spec(cfg, outbound_id, to=str(target))
    forbidden = ("architecture", "style-guide", "style_guide")
    for p in written:
        assert not any(f in p.name.lower() for f in forbidden)


# ---- --emit narrows the run ----------------------------------------------------------

def test_emit_narrows_REMOVED_to_task_spec_only(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _epic_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"

    written = E.export_spec(cfg, outbound_id, to=str(target), emit=["task-spec"])
    assert all(p.name != "project-plan.md" for p in written)
    assert not (target / "project-plan.md").exists()
    assert len(written) == 2


def test_emit_unknown_artifact_raises(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _feature_fixture(cfg, tmp_path)
    with pytest.raises(ValueError, match="nothing to emit"):
        E.export_spec(cfg, outbound_id, to=str(tmp_path / "t"), emit=["prd"])


# ---- non-clobbering: owned task-spec file --------------------------------------------

def test_owned_file_reexport_identical_is_idempotent(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _feature_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"

    w1 = E.export_spec(cfg, outbound_id, to=str(target))
    w2 = E.export_spec(cfg, outbound_id, to=str(target))
    assert w1 == w2
    assert w1[0].exists()


def test_owned_file_refuses_divergent_overwrite_without_force(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _feature_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"
    written = E.export_spec(cfg, outbound_id, to=str(target))
    task_path = written[0]

    task_path.write_text(task_path.read_text() + "\nHand-edited by the target repo's PM.\n")

    with pytest.raises(ValueError, match="different content"):
        E.export_spec(cfg, outbound_id, to=str(target))

    E.export_spec(cfg, outbound_id, to=str(target), force=True)
    assert "Hand-edited" not in task_path.read_text()


def test_project_plan_splice_refuses_divergent_without_force(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _epic_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"
    E.export_spec(cfg, outbound_id, to=str(target))

    plan_path = target / "specs" / "project-plan.md"
    plan_path.write_text(plan_path.read_text().replace("Adversarial reviewer", "Renamed task"))

    with pytest.raises(ValueError, match="different content"):
        E.export_spec(cfg, outbound_id, to=str(target))

    E.export_spec(cfg, outbound_id, to=str(target), force=True)
    assert "Renamed task" not in plan_path.read_text()


# ---- declarative TemplateScheme (manifest tier, no Python) ---------------------------

def test_template_scheme_plain_md_renders_manifest_remap(tmp_path):
    cfg = _cfg(tmp_path)
    _, outbound_id = _feature_fixture(cfg, tmp_path)
    target = tmp_path / "plain-target"

    written = E.export_spec(cfg, outbound_id, scheme="plain-md", to=str(target))
    assert len(written) == 1
    text = written[0].read_text()
    assert "## Overview" in text
    assert "## Goals" in text
    assert "## Acceptance" in text
    assert "- [ ] Reviewer flags contradictions" in text
    assert "## Verification" in text


def test_template_scheme_validate_blocks_missing_required_field(tmp_path):
    cfg = _cfg(tmp_path)
    path, outbound_id = _scaffold(cfg, "acme", "No acceptance")
    text = path.read_text().replace(
        "## Acceptance criteria\n\n<What must be TRUE for this to be correct. Each item must "
        "be objectively checkable.>\n\n- [ ] …\n- [ ] …",
        "## Acceptance criteria\n\n")
    path.write_text(text)

    with pytest.raises(ValueError, match="fails validation"):
        E.export_spec(cfg, outbound_id, scheme="plain-md", to=str(tmp_path / "target"))


# ---- SPEC-0034: auto-allocate free Task-IDs ----------------------------------------

def test_REMOVED_bumps_task_id_when_preferred_taken(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.1"}})
    _, outbound_id = _feature_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"
    tasks = target / "specs" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "1.1.1-already-there.md").write_text(
        "# Task Spec: 1.1.1 — Already\n\nSource: wt outbound spec `OTHER-0001`.\n",
        encoding="utf-8",
    )

    written = E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target))
    assert len(written) == 1
    assert written[0].name.startswith("1.1.2-"), written[0].name
    assert "1.1.1-" not in written[0].name
    assert f"Source: wt outbound spec `{outbound_id}`." in written[0].read_text()


def test_REMOVED_sequential_features_get_distinct_ids(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.1"}})
    target = tmp_path / "tc-target"

    _, id_a = _scaffold(cfg, "sdlcbundle-REMOVED", "First feature")
    _fill_acceptance_and_test_plan(
        _find_outbound(cfg, id_a),
        ["I can use feature A"],
        ["- **Automated tests:** `uv run pytest`",
         "- **Manual verification:** look.",
         "- **Regression guard:** green."])
    _, id_b = _scaffold(cfg, "sdlcbundle-REMOVED", "Second feature")
    _fill_acceptance_and_test_plan(
        _find_outbound(cfg, id_b),
        ["I can use feature B"],
        ["- **Automated tests:** `uv run pytest`",
         "- **Manual verification:** look.",
         "- **Regression guard:** green."])

    w1 = E.export_spec(cfg, id_a, scheme="REMOVED", to=str(target))
    w2 = E.export_spec(cfg, id_b, scheme="REMOVED", to=str(target))
    assert w1[0].name.startswith("1.1.1-")
    assert w2[0].name.startswith("1.1.2-")
    assert w1[0].name != w2[0].name


def test_REMOVED_reexport_reuses_prior_task_id(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.1"}})
    _, outbound_id = _feature_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"
    tasks = target / "specs" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "1.1.1-occupied.md").write_text(
        "# Task Spec: 1.1.1 — Occ\n\nSource: wt outbound spec `OTHER-9`.\n",
        encoding="utf-8",
    )

    first = E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target))
    assert first[0].name.startswith("1.1.2-")
    second = E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target))
    assert second[0] == first[0]
    assert second[0].name.startswith("1.1.2-")


# ---- SPEC-0037: explicit task_id pin ------------------------------------------------

def test_REMOVED_fm_task_id_pin_when_free(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.1"}})
    path, outbound_id = _feature_fixture(cfg, tmp_path)
    # inject frontmatter task_id
    text = path.read_text()
    path.write_text(text.replace("scope_paths: src/review/",
                                 "scope_paths: src/review/\ntask_id: \"1.3.2\""))
    target = tmp_path / "tc-target"
    tasks = target / "specs" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "1.3.1-prior.md").write_text(
        "# Task Spec: 1.3.1\n\nSource: wt outbound spec `OTHER-1`.\n", encoding="utf-8")
    (tasks / "1.4.1-next.md").write_text(
        "# Task Spec: 1.4.1\n\nSource: wt outbound spec `OTHER-2`.\n", encoding="utf-8")

    written = E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target))
    assert written[0].name.startswith("1.3.2-"), written[0].name


def test_REMOVED_cli_task_id_overrides_fm(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.1"}})
    path, outbound_id = _feature_fixture(cfg, tmp_path)
    text = path.read_text()
    path.write_text(text.replace("scope_paths: src/review/",
                                 "scope_paths: src/review/\ntask_id: \"1.3.2\""))
    target = tmp_path / "tc-target"
    written = E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target),
                            task_id="1.5.1")
    assert written[0].name.startswith("1.5.1-"), written[0].name


def test_REMOVED_pinned_id_clash_fails(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.1"}})
    _, outbound_id = _feature_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"
    tasks = target / "specs" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "1.3.2-occupied.md").write_text(
        "# Task Spec: 1.3.2\n\nSource: wt outbound spec `OTHER-9`.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="already taken"):
        E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target),
                      task_id="1.3.2")
    assert not any(tasks.glob("1.3.2-adversarial*"))


def test_REMOVED_reexport_ignores_fm_pin_keeps_source(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.1"}})
    path, outbound_id = _feature_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"
    first = E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target))
    assert first[0].name.startswith("1.1.1-")
    # Later add fm pin to a different id — re-export without --task-id must keep 1.1.1
    text = path.read_text()
    if "task_id:" not in text:
        path.write_text(text.replace("scope_paths: src/review/",
                                     "scope_paths: src/review/\ntask_id: \"9.9.9\""))
    second = E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target))
    assert second[0] == first[0]
    assert second[0].name.startswith("1.1.1-")


def test_REMOVED_epic_rejects_task_id_pin(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _epic_fixture(cfg, tmp_path)
    target = tmp_path / "tc-target"
    with pytest.raises(ValueError, match="feature-only"):
        E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target),
                      task_id="1.2.1")


def test_wt_native_ignores_task_id(tmp_path):
    cfg = _cfg(tmp_path)
    path, outbound_id = _scaffold(cfg, "acme", "Native ignore pin")
    text = path.read_text()
    path.write_text(text.replace("---\n", "---\ntask_id: \"1.3.2\"\n", 1)
                    if "task_id:" not in text
                    else text)
    # simpler: append via _scaffold pattern
    text = path.read_text()
    fm, body = text.split("---\n", 2)[1:]
    if "task_id:" not in fm:
        path.write_text("---\n" + fm.rstrip() + "\ntask_id: \"1.3.2\"\n---\n" + body)
    dest_spec, _ = E.export_spec(cfg, outbound_id, scheme="wt-native",
                                 to=str(tmp_path / "native-target"), task_id="9.9.9")
    assert dest_spec.exists()


def _find_outbound(cfg, outbound_id):
    from wt.export import _find_outbound_spec
    return _find_outbound_spec(cfg, outbound_id)


# ---- CLI (`wt spec export --scheme/--emit`, `wt spec schemes`) -----------------------

def test_cli_spec_schemes_lists_builtins():
    from click.testing import CliRunner
    from wt.cli import cli
    r = CliRunner().invoke(cli, ["spec", "schemes"])
    assert r.exit_code == 0, r.output
    assert "wt-native" in r.output
    assert "REMOVED" in r.output
    assert "plain-md" in r.output


def test_cli_spec_export_with_scheme_and_emit(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.2"}})
    _, outbound_id = _epic_fixture(cfg, tmp_path)
    import wt.cli as cli_mod
    monkeypatch.setattr(cli_mod, "load_config", lambda: cfg)

    from click.testing import CliRunner
    target = tmp_path / "cli-target"
    r = CliRunner().invoke(cli_mod.cli, ["spec", "export", outbound_id, "--to", str(target),
                                        "--emit", "task-spec"])
    assert r.exit_code == 0, r.output
    assert "exported" in r.output
    assert not (target / "project-plan.md").exists()
    assert (target / "specs" / "tasks" / "1.2.1-adversarial-reviewer.md").exists()


# ---- SPEC-0047 compose parent: children --------------------------------------------

def test_REMOVED_epic_composes_parent_children(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "2.0"}})
    epic_path, epic_id = _epic_fixture(cfg, tmp_path)
    child_a, id_a = S.scaffold_outbound(cfg, "sdlcbundle-REMOVED", title="Child Alpha")
    text = child_a.read_text().replace(f"id: {id_a}\n", f"id: {id_a}\nparent: {epic_id}\n", 1)
    if f"parent: {epic_id}" not in text:
        text = child_a.read_text().replace(f"id: {id_a}", f"id: {id_a}\nparent: {epic_id}", 1)
    child_a.write_text(text)
    _fill_acceptance_and_test_plan(
        child_a,
        ["I can use child alpha"],
        ["- **Automated tests:** `uv run pytest`",
         "- **Manual verification:** alpha.",
         "- **Regression guard:** green."])
    child_b, id_b = S.scaffold_outbound(cfg, "sdlcbundle-REMOVED", title="Child Beta")
    text = child_b.read_text().replace(f"id: {id_b}", f"id: {id_b}\nparent: {epic_id}", 1)
    text = text.replace("## Decision\n\n<", "## Decision\n\nBeta-only decision text.\n\n<", 1)
    child_b.write_text(text)
    _fill_acceptance_and_test_plan(
        child_b,
        ["I can use child beta"],
        ["- **Automated tests:** `uv run pytest`",
         "- **Manual verification:** beta.",
         "- **Regression guard:** green."])

    target = tmp_path / "tc-target"
    written = E.export_spec(cfg, epic_id, scheme="REMOVED", to=str(target))
    names = sorted(p.name for p in written)
    assert "project-plan.md" in names
    task_names = [n for n in names if n != "project-plan.md"]
    assert any("child-alpha" in n for n in task_names)
    assert any("child-beta" in n for n in task_names)
    alpha = next(p for p in written if "child-alpha" in p.name)
    assert "I can use child alpha" in alpha.read_text()
    beta = next(p for p in written if "child-beta" in p.name)
    assert "Beta-only decision text" in beta.read_text()
    assert not any("adversarial-reviewer" in n for n in task_names)


# ---- SPEC-0048 outcome signal ------------------------------------------------------

def test_has_outcome_signal_helper():
    from wt.export_schemes.canonical import CanonicalSpec, has_outcome_signal
    base = dict(id="X-1", title="t", kind="feature", context="c", goals=[], non_goals=[],
                decision="d", design="", acceptance=[], test_plan="tp", depends_on=[])
    assert not has_outcome_signal(CanonicalSpec(**base))
    assert has_outcome_signal(CanonicalSpec(**{**base, "outcome": "Users can triage"}))
    assert has_outcome_signal(CanonicalSpec(**{**base, "acceptance": ["I can filter sessions"]}))
    assert has_outcome_signal(CanonicalSpec(**{**base, "acceptance": ["User can export CSV"]}))


def test_REMOVED_rejects_missing_outcome_unless_force(tmp_path):
    cfg = _cfg(tmp_path, outbox_targets={
        "sdlcbundle-REMOVED": {"scheme": "REMOVED", "task_base": "1.1"}})
    path, outbound_id = _scaffold(cfg, "sdlcbundle-REMOVED", "No outcome")
    _fill_acceptance_and_test_plan(
        path,
        ["File exists on disk"],
        ["- **Automated tests:** `uv run pytest`",
         "- **Manual verification:** look.",
         "- **Regression guard:** green."])
    target = tmp_path / "tc-target"
    with pytest.raises(ValueError, match="product-fit outcome"):
        E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target))
    written = E.export_spec(cfg, outbound_id, scheme="REMOVED", to=str(target), force=True)
    assert written


# ---- SPEC-0058 user-config-dir manifest loading ------------------------------------

_PLAIN_MD_MANIFEST = '''
name = "plain-md"
description = "user override"
required_fields = ["id", "title", "context", "acceptance"]
naming = "{id}-{slug}.md"
artifact = "spec"

[[sections]]
label = "Overview override"
source = "context"
'''

_DEMO_MANIFEST = '''
name = "demo-user-scheme"
description = "a user-dropped scheme"
required_fields = ["id", "title", "context"]
naming = "{id}-{slug}.md"
artifact = "spec"

[[sections]]
label = "Body"
source = "context"
'''


def test_load_manifests_from_missing_dir_is_noop(tmp_path):
    from wt.export_schemes.template_scheme import load_manifests_from
    assert load_manifests_from(tmp_path / "does-not-exist", origin="user-config") == []


def test_load_manifests_from_reads_toml_and_stamps_origin(tmp_path):
    from wt.export_schemes.template_scheme import load_manifests_from
    schemes_dir = tmp_path / "schemes"
    schemes_dir.mkdir()
    (schemes_dir / "demo.toml").write_text(_DEMO_MANIFEST)
    loaded = load_manifests_from(schemes_dir, origin="user-config")
    assert len(loaded) == 1
    assert loaded[0].name == "demo-user-scheme"
    assert loaded[0].origin == "user-config"


def test_user_config_scheme_registers_and_overrides_builtin(tmp_path, monkeypatch):
    """Integration: a WT_CONFIG_DIR/schemes/*.toml is picked up on (re)import and a same-named
    manifest overrides the shipped built-in (SPEC-0058)."""
    import importlib
    from wt import export_schemes as ES
    from wt.export_schemes import template_scheme as TS

    schemes_dir = tmp_path / "schemes"
    schemes_dir.mkdir()
    (schemes_dir / "demo.toml").write_text(_DEMO_MANIFEST)
    (schemes_dir / "plain-md.toml").write_text(_PLAIN_MD_MANIFEST)

    snapshot = dict(ES._REGISTRY)
    monkeypatch.setenv("WT_CONFIG_DIR", str(tmp_path))
    try:
        importlib.reload(TS)
        names = {s.name for s in ES.available()}
        assert "demo-user-scheme" in names
        demo = ES.get("demo-user-scheme")
        assert demo.origin == "user-config"

        overridden = ES.get("plain-md")
        assert overridden.origin == "user-config"
        assert overridden.description == "user override"
    finally:
        ES._REGISTRY.clear()
        ES._REGISTRY.update(snapshot)
        monkeypatch.delenv("WT_CONFIG_DIR", raising=False)
        importlib.reload(TS)


def test_cli_spec_schemes_shows_user_config_origin(tmp_path, monkeypatch):
    import importlib
    from click.testing import CliRunner
    from wt import export_schemes as ES
    from wt.export_schemes import template_scheme as TS
    from wt.cli import cli

    schemes_dir = tmp_path / "schemes"
    schemes_dir.mkdir()
    (schemes_dir / "demo.toml").write_text(_DEMO_MANIFEST)

    snapshot = dict(ES._REGISTRY)
    monkeypatch.setenv("WT_CONFIG_DIR", str(tmp_path))
    try:
        importlib.reload(TS)
        r = CliRunner().invoke(cli, ["spec", "schemes"])
        assert r.exit_code == 0, r.output
        assert "demo-user-scheme" in r.output
        assert "[user-config]" in r.output
        wt_native_line = next(ln for ln in r.output.splitlines() if "wt-native" in ln)
        assert "[user-config]" not in wt_native_line
    finally:
        ES._REGISTRY.clear()
        ES._REGISTRY.update(snapshot)
        monkeypatch.delenv("WT_CONFIG_DIR", raising=False)
        importlib.reload(TS)


# ---- SPEC-0059 static sections + {{field}} placeholder substitution ----------------

def _canon(**over):
    from wt.export_schemes.canonical import CanonicalSpec
    base = dict(id="X-1", title="Sample", kind="feature", context="ctx text", goals=["g1"],
                non_goals=[], decision="dec text", design="", acceptance=["a1", "a2"],
                test_plan="tp", depends_on=[])
    base.update(over)
    return CanonicalSpec(**base)


def _render_one(manifest, spec):
    from wt.export_schemes.template_scheme import TemplateScheme
    scheme = TemplateScheme(manifest)

    class Ctx:
        pass
    ctx = Ctx()
    ctx.canonical = spec
    return scheme.render(ctx, {})[0].content


def test_static_section_verbatim_no_placeholders():
    m = {"name": "s", "sections": [{"label": "Fixed", "static": "always the same text"}]}
    content = _render_one(m, _canon())
    assert "## Fixed\n\nalways the same text" in content


def test_static_section_substitutes_string_field():
    m = {"name": "s", "sections": [{"label": "Ctx", "static": "Symptom: {{context}}"}]}
    content = _render_one(m, _canon(context="the bug"))
    assert "Symptom: the bug" in content


def test_static_section_substitutes_list_field_as_bullets():
    m = {"name": "s", "sections": [{"label": "Goals", "static": "{{goals}}"}]}
    content = _render_one(m, _canon(goals=["do X", "do Y"]))
    assert "- do X\n- do Y" in content


def test_static_section_checkbox_placeholder():
    m = {"name": "s", "sections": [{"label": "AC", "static": "{{acceptance:checkbox}}"}]}
    content = _render_one(m, _canon(acceptance=["works"]))
    assert "- [ ] works" in content


def test_static_section_mixes_fixed_text_and_placeholder():
    m = {"name": "s", "sections": [
        {"label": "AC", "static": "{{acceptance:checkbox}}\n\n- [ ] CI green (fixed)"}]}
    content = _render_one(m, _canon(acceptance=["thing works"]))
    assert "- [ ] thing works" in content
    assert "- [ ] CI green (fixed)" in content


def test_static_section_missing_field_renders_fill():
    m = {"name": "s", "sections": [{"label": "X", "static": "{{scope_paths}}"}]}
    content = _render_one(m, _canon())
    assert "<!-- fill -->" in content


def test_REMOVED_extended_manifest_renders_full_shape():
    """SPEC-0059: the vendored example manifest (docs/examples/schemes/REMOVED-extended.toml)
    loads, interleaves fixed boilerplate with wt-sourced content, and lands under
    specs/tasks/ (naming stays wt-id-based; no X.Y.Z Task-ID allocation, per Non-goals)."""
    from wt.export_schemes.template_scheme import TemplateScheme, _load_manifest

    manifest_path = ROOT / "docs" / "examples" / "schemes" / "REMOVED-extended.toml"
    scheme = TemplateScheme(_load_manifest(manifest_path))
    assert scheme.name == "REMOVED-extended"

    spec = _canon(id="DEMO-0001", title="Fix gimbal comms timeout",
                 context="Gimbal comms drops after 30s idle.",
                 goals=["Comms stays alive past 30s idle"],
                 decision="Reset the keepalive timer.", design="Touches linux_gimbal/ only.",
                 acceptance=["Idle comms survive 5min soak test"],
                 depends_on=["DEMO-0000 (branch setup)"],
                 verification_commands="pytest ats_tests/test_gimbal_idle.py -v")
    out = _render_one({**_load_manifest(manifest_path)}, spec)

    assert "Gimbal comms drops after 30s idle" in out      # wt-sourced Context
    assert "layer-dependency-flow" in out                  # fixed Architectural Contracts
    assert "- Comms stays alive past 30s idle" in out       # wt-sourced functional requirement
    assert "mcu-stm32-testing" in out                       # fixed NFR preset boilerplate
    assert "- [ ] Idle comms survive 5min soak test" in out  # wt-sourced AC (checkbox)
    assert "HIL_FAILED" in out                              # fixed AC boilerplate
    assert "pytest ats_tests/test_gimbal_idle.py -v" in out  # substituted verification command
    assert "DEMO-0000 (branch setup)" in out                # wt-sourced dependency

    ctx_relpath_scheme = TemplateScheme(_load_manifest(manifest_path))

    class Ctx:
        pass
    ctx = Ctx()
    ctx.canonical = spec
    files = ctx_relpath_scheme.render(ctx, {})
    assert files[0].relpath == "specs/tasks/DEMO-0001-fix-gimbal-comms-timeout.md"


def test_REMOVED_extended_manifest_is_config_dir_installable(tmp_path, monkeypatch):
    """The example manifest, once copied into WT_CONFIG_DIR/schemes/, is picked up exactly
    like any other user-config scheme (SPEC-0058 mechanism) — no wt core change (SPEC-0059)."""
    import importlib
    import shutil
    from wt import export_schemes as ES
    from wt.export_schemes import template_scheme as TS

    manifest_path = ROOT / "docs" / "examples" / "schemes" / "REMOVED-extended.toml"
    schemes_dir = tmp_path / "schemes"
    schemes_dir.mkdir()
    shutil.copy(manifest_path, schemes_dir / "REMOVED-extended.toml")

    snapshot = dict(ES._REGISTRY)
    monkeypatch.setenv("WT_CONFIG_DIR", str(tmp_path))
    try:
        importlib.reload(TS)
        scheme = ES.get("REMOVED-extended")
        assert scheme.origin == "user-config"
    finally:
        ES._REGISTRY.clear()
        ES._REGISTRY.update(snapshot)
        monkeypatch.delenv("WT_CONFIG_DIR", raising=False)
        importlib.reload(TS)


# ---- Regression: wt.export / REMOVED must not depend on jsonschema at runtime ---

def test_export_module_has_no_runtime_jsonschema_dependency(monkeypatch):
    """`tools/spec_lint.py` requires jsonschema (a dev-only dependency); wt.export and
    wt.export_schemes.REMOVED previously exec-loaded that file at runtime just to reuse
    split_frontmatter/sections (the same class of bug SPEC-0001/commit 6b0b4b9 fixed for
    cli.py's promote path — it recurred independently in export.py and REMOVED.py). Both
    must use wt.specmeta (the runtime-safe extraction) instead, so the installed `wt` binary
    (whose venv has no jsonschema) doesn't crash on `wt spec export`."""
    import builtins
    import importlib
    import sys

    real_import = builtins.__import__

    def blocked_import(name, *a, **k):
        if name == "jsonschema" or name.startswith("jsonschema."):
            raise ModuleNotFoundError("No module named 'jsonschema'")
        return real_import(name, *a, **k)

    for mod in ("wt.export", "wt.export_schemes.REMOVED", "wt.export_schemes.canonical"):
        sys.modules.pop(mod, None)
    monkeypatch.setattr(builtins, "__import__", blocked_import)
    try:
        importlib.import_module("wt.export")
        importlib.import_module("wt.export_schemes.REMOVED")
    finally:
        monkeypatch.undo()
        for mod in ("wt.export", "wt.export_schemes.REMOVED", "wt.export_schemes.canonical"):
            sys.modules.pop(mod, None)
        importlib.import_module("wt.export")


# ---- IDEA-263: wrapped bullet continuation lines --------------------------------------

def test_canonical_bullets_joins_wrapped_continuation_lines():
    """Bug found in a real spec (EXAMPLE-0030's Goals section): a hand-wrapped bullet's second
    physical line, indented with no leading `-`, was silently dropped instead of joined back
    onto the bullet — truncating the exported Functional Requirement mid-sentence."""
    from wt.export_schemes.canonical import _bullets
    text = ("- Every batch of a multi-batch session appears in the step summary, the Slack "
            "message, and the\n"
            "  consumer PR fan-in row — not just one arbitrarily-picked batch.\n"
            "- Reuse the existing, already-correct manifest-driven iteration (the Check Runs "
            "path) as the\n"
            "  template, rather than inventing a new batch-discovery mechanism.\n")
    items = _bullets(text)
    assert items == [
        "Every batch of a multi-batch session appears in the step summary, the Slack message, "
        "and the consumer PR fan-in row — not just one arbitrarily-picked batch.",
        "Reuse the existing, already-correct manifest-driven iteration (the Check Runs path) "
        "as the template, rather than inventing a new batch-discovery mechanism.",
    ]


def test_specs_bullet_items_joins_wrapped_continuation_lines():
    """Same fix, internal wt.specs copy (used by spec_tasks for org task generation)."""
    from wt.specs import _bullet_items
    text = ("- A single-batch session (today's common case) renders identically to current "
            "behavior (no\n"
            "  regression for the non-multi-batch path).\n")
    assert _bullet_items(text) == [
        "A single-batch session (today's common case) renders identically to current "
        "behavior (no regression for the non-multi-batch path).",
    ]


def test_canonical_bullets_blank_line_resets_continuation():
    """A blank line marks a paragraph break (e.g. between **Goals** and **Non-goals**) and
    must not merge into the previous bullet."""
    from wt.export_schemes.canonical import _split_goals
    text = ("**Goals**\n"
            "- First goal.\n"
            "\n"
            "**Non-goals**\n"
            "- First non-goal.\n")
    goals, non_goals = _split_goals(text)
    assert goals == ["First goal."]
    assert non_goals == ["First non-goal."]


def test_REMOVED_verification_steps_joins_wrapped_test_plan_bullets():
    """Bug found in a real spec (EXAMPLE-0030's Test plan): wrapped continuation lines of a
    labeled bullet (`- **Automated tests:** …`) matched neither the label regex nor "blank",
    so they were misfiled as separate unlabeled prose fragments — scattering one sentence
    across several out-of-order, mis-numbered Manual Verification list items."""
    from wt.export_schemes.REMOVED import _verification_steps
    text = ("- **Manual verification:** trigger a real device-test-dispatch run configured "
            "with 2+ batches on\n"
            "  a bench node; inspect the posted step summary, Slack message, and (if a "
            "trigger repo is\n"
            "  available) the consumer PR comment to confirm every batch appears.\n")
    rendered = _verification_steps(text)
    assert ("1. trigger a real device-test-dispatch run configured with 2+ batches on a bench "
            "node; inspect the posted step summary, Slack message, and (if a trigger repo is "
            "available) the consumer PR comment to confirm every batch appears.") in rendered
    assert "2." not in rendered.split("### Manual Verification")[1]
