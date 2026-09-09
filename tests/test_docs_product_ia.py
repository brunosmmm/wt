"""SPEC-0142: docs/product IA tree + home narrative keywords."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCT = ROOT / "docs" / "product"

REQUIRED = [
    "index.md",
    "concepts/index.md",
    "guides/index.md",
    "guides/getting-started.md",
    "guides/track-time.md",
    "guides/idea-to-ship.md",
    "guides/outbound.md",
    "guides/multi-project.md",
    "capabilities/index.md",
    "capabilities/report.md",
    "capabilities/ideas.md",
    "capabilities/tui.md",
    "capabilities/hub.md",
    "capabilities/projects.md",
    "capabilities/sheet.md",
    "capabilities/clock.md",
    "capabilities/completion.md",
    "capabilities/release-archive.md",
    "capabilities/tasks-agenda.md",
    "capabilities/meetings.md",
    "capabilities/skills.md",
    "reference/index.md",
    "contribute/index.md",
]


def test_docs_product_ia_tree_exists():
    missing = [p for p in REQUIRED if not (PRODUCT / p).is_file()]
    assert not missing, f"missing docs/product paths: {missing}"


def test_home_locks_dual_capability_and_clock_wording():
    home = (PRODUCT / "index.md").read_text(encoding="utf-8").lower()
    assert "passive time tracking" in home or "passive" in home and "time" in home
    assert "idea" in home and ("ship" in home or "spec" in home)
    assert "clock-in" in home or "clock in" in home
    assert "supplemental" in home


def test_glossary_has_core_terms():
    gloss = (PRODUCT / "concepts" / "index.md").read_text(encoding="utf-8").lower()
    for term in ("topic", "idea", "spec", "outbound", "hub", "desk", "clock-in", "facet"):
        assert term in gloss, f"glossary missing {term!r}"
