"""SPEC-0144: product guides are non-stub and cover core workflows."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDES = ROOT / "docs" / "product" / "guides"

REQUIRED_PHRASES = {
    "getting-started.md": ["uv tool install", "wt topics --unmapped", "wt idea"],
    "track-time.md": ["wt report --week", "wt snapshot", "passive"],
    "idea-to-ship.md": ["wt spec new", "wt spec generate", "wt next"],
    "outbound.md": ["wt projects add", "wt spec export", "pull-status"],
    "multi-project.md": ["wt projects --json", "fan"],
}


def test_guides_are_not_stubs():
    for name in REQUIRED_PHRASES:
        text = (GUIDES / name).read_text(encoding="utf-8")
        assert "**Status:** stub" not in text, f"{name} still stub"
        assert len(text) > 400, f"{name} too short"


def test_guides_cover_key_commands():
    for name, phrases in REQUIRED_PHRASES.items():
        text = (GUIDES / name).read_text(encoding="utf-8")
        for phrase in phrases:
            assert phrase in text, f"{name} missing {phrase!r}"


def test_guides_index_lists_five():
    index = (GUIDES / "index.md").read_text(encoding="utf-8")
    assert "**Status:** stub" not in index
    for slug in (
        "getting-started.md",
        "track-time.md",
        "idea-to-ship.md",
        "outbound.md",
        "multi-project.md",
    ):
        assert slug in index
