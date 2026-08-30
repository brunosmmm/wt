"""Policy: no MCP packaging in core (SPEC-0053)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_has_no_mcp_extra():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "mcp" not in text.lower()
    assert not (ROOT / "src" / "wt" / "mcp.py").exists()
    assert not list((ROOT / "src" / "wt").glob("mcp*"))
