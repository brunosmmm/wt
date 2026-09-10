"""wt hub --json triage (SPEC-0052)."""
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from click.testing import CliRunner

from wt import org_write as W
from wt import specs as S
from wt.cli import cli

ROOT = Path(__file__).resolve().parent.parent


def _cfg(tmp_path):
    org = tmp_path / "org"
    org.mkdir()
    data = tmp_path / "data"
    data.mkdir()
    specs = tmp_path / "specs"
    specs.mkdir()
    for name in ("TEMPLATE.md", "TEMPLATE-epic.md"):
        (specs / name).write_text((ROOT / "docs" / "specs" / name).read_text())
    return {
        "org_files": [str(org)],
        "org_todo_keywords": ["TODO", "|", "DONE"],
        "org_idea_keywords": [
            "IDEA", "INCUBATE", "SPECCED", "|", "PROMOTED", "EXPORTED", "DROPPED",
        ],
        "timezone": "America/New_York",
        "_tz": ZoneInfo("America/New_York"),
        "data_dir": str(data),
        "org_capture_file": str(org / "inbox.org"),
        "org_ideas_file": str(org / "ideas.org"),
        "specs_dir": str(specs),
        "config_dir": str(tmp_path / "config"),
        "outbox_dir": str(tmp_path / "outbox"),
        "outbox_targets": {},
        "project_axis": "bucket",
        "hub_noise_states": ["CATEGORIZE"],
        "hub_tasks_cap": 40,
    }


def _patch(monkeypatch, cfg):
    monkeypatch.setattr("wt.cli.load_config", lambda: cfg)


def test_hub_requires_json(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    _patch(monkeypatch, cfg)
    r = CliRunner().invoke(cli, ["hub"])
    assert r.exit_code != 0
    assert "--json" in r.output


def test_hub_json_envelope(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    W.add_idea(cfg, "hub idea", state="IDEA")

    # active internal
    (Path(cfg["specs_dir"]) / "0001-active.md").write_text(
        "---\nid: SPEC-0001\ntitle: \"Active\"\nstatus: draft\n"
        "kind: feature\nmilestone: M1\ncreated: 2026-07-01\nupdated: 2026-07-01\n---\n\n"
        "## Summary\n\nx\n",
        encoding="utf-8",
    )
    # done — must be omitted
    (Path(cfg["specs_dir"]) / "0002-done.md").write_text(
        "---\nid: SPEC-0002\ntitle: \"Done\"\nstatus: done\n"
        "kind: feature\nmilestone: M1\ncreated: 2026-07-01\nupdated: 2026-07-01\n---\n\n"
        "## Summary\n\nx\n",
        encoding="utf-8",
    )

    out_path, oid = S.scaffold_outbound(cfg, "acme", title="Outbound stub")
    ledger = ROOT / "docs" / "LEDGER.md"
    before = ledger.read_text(encoding="utf-8") if ledger.exists() else None

    _patch(monkeypatch, cfg)
    r = CliRunner().invoke(cli, ["hub", "--json"])
    assert r.exit_code == 0, r.output
    data = json.loads(r.output)
    assert data["schema"] == "wt.hub.v1"
    assert {i["id"] for i in data["ideas"]} == {"IDEA-001"}
    assert {s["id"] for s in data["internal"]} == {"SPEC-0001"}
    assert data["internal"][0]["status"] == "draft"
    assert len(data["outbound"]) == 1
    assert data["outbound"][0]["id"] == oid
    assert data["outbound"][0]["project"] == "acme"
    assert data["outbound"][0]["path"] == str(out_path)
    assert "today" in data
    assert "date" in data["today"]
    assert "overdue" in data["today"] and "tasks" in data["today"]

    if before is not None:
        assert ledger.read_text(encoding="utf-8") == before


def test_hub_today_slice_membership_and_noise(tmp_path, monkeypatch):
    import datetime as dt

    cfg = _cfg(tmp_path)
    cfg["org_todo_keywords"] = ["TODO", "CATEGORIZE", "|", "DONE"]
    today = dt.datetime.now(cfg["_tz"]).date().isoformat()
    W.add_task(cfg, "due today", scheduled=today)
    W.add_task(cfg, "late work", deadline="2020-01-01")
    W.add_task(cfg, "noise dated", state="CATEGORIZE", scheduled=today)
    W.add_idea(cfg, "idea scheduled", scheduled=today)
    _patch(monkeypatch, cfg)
    r = CliRunner().invoke(cli, ["hub", "--json"])
    assert r.exit_code == 0, r.output
    data = json.loads(r.output)
    assert data["today"]["date"] == today
    heads = {t["heading"] for t in data["today"]["tasks"]}
    assert "due today" in heads
    assert "noise dated" not in heads
    assert "idea scheduled" not in heads
    overdue_heads = {t["heading"] for t in data["today"]["overdue"]}
    assert "late work" in overdue_heads


def test_hub_tasks_slice_open_and_none(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    cfg["hub_tasks_cap"] = 2
    cfg["org_todo_keywords"] = ["TODO", "CATEGORIZE", "|", "DONE"]
    W.add_task(cfg, "a one")
    W.add_task(cfg, "b two")
    W.add_task(cfg, "c three")
    W.add_task(cfg, "noise", state="CATEGORIZE")
    _patch(monkeypatch, cfg)
    r = CliRunner().invoke(cli, ["hub", "--json", "--tasks-slice", "open"])
    assert r.exit_code == 0, r.output
    data = json.loads(r.output)
    assert data["today"]["slice"] == "open"
    assert len(data["today"]["tasks"]) == 2
    assert all(t["heading"] != "noise" for t in data["today"]["tasks"])
    r = CliRunner().invoke(cli, ["hub", "--json", "--tasks-slice", "none"])
    assert r.exit_code == 0, r.output
    data = json.loads(r.output)
    assert "today" not in data


def test_hub_help_documents_json():
    r = CliRunner().invoke(cli, ["hub", "--help"])
    assert r.exit_code == 0
    assert "--json" in r.output
    assert "--tasks-slice" in r.output
