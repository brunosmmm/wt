"""SPEC-0145: capability showcase pages are non-stub."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAPS = ROOT / "docs" / "product" / "capabilities"

REQUIRED = {
    "report.md": ["wt report", "wt topics", "wt snapshot"],
    "ideas.md": ["wt ideas", "wt next", "wt idea"],
    "tui.md": ["wt tui", "tui"],
    "hub.md": ["wt hub", "--json"],
    "projects.md": ["wt projects", "wt spec export"],
    "sheet.md": ["wt sheet", "plan"],
    "clock.md": ["clock-in", "supplemental"],
    "completion.md": ["wt completion", "fish"],
    "release-archive.md": ["wt release-archive"],
    "tasks-agenda.md": ["wt tasks", "wt agenda", "wt add"],
    "meetings.md": ["wt refresh-meetings"],
    "skills.md": ["wt skills install", "/wt-orient"],
}


def test_capability_pages_not_stubs():
    for name in REQUIRED:
        text = (CAPS / name).read_text(encoding="utf-8")
        assert "**Status:** stub" not in text, name
        assert len(text) > 250, name


def test_capability_pages_key_phrases():
    for name, phrases in REQUIRED.items():
        text = (CAPS / name).read_text(encoding="utf-8")
        for phrase in phrases:
            assert phrase in text, f"{name} missing {phrase!r}"


def test_capabilities_index_not_stub_language():
    index = (CAPS / "index.md").read_text(encoding="utf-8")
    assert "IDEA-358" not in index
    assert "short scope card" not in index
    for name in REQUIRED:
        assert name in index
