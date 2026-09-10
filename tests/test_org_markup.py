"""Org ↔ Markdown body helpers (SPEC-0030)."""
from wt.org_markup import from_org_body, to_org_body


def test_to_org_backticks_and_bold():
    assert to_org_body("use `wt-native` here") == "use ~wt-native~ here"
    assert to_org_body("This is **not** inventing") == "This is *not* inventing"
    assert to_org_body("also __bold__ ok") == "also *bold* ok"


def test_to_org_strips_atx_and_fences():
    assert to_org_body("## Summary title\n") == "Summary title\n"
    src = "before\n```bash\necho hi\n```\nafter\n"
    out = to_org_body(src)
    assert "```" not in out
    assert "echo hi" in out
    assert "before" in out and "after" in out


def test_to_org_idempotent_on_org():
    org = "use ~wt-native~ and *not* inventing\n"
    assert to_org_body(org) == org


def test_from_org_preserves_headlines():
    text = "** Summary\nuse ~code~ and *bold* here\n"
    out = from_org_body(text)
    assert out.startswith("** Summary\n")
    assert "`code`" in out
    assert "**bold**" in out


def test_from_org_verbatim():
    assert "`x`" in from_org_body("=x=\n")
