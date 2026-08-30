"""Light Markdown ↔ org markup helpers for idea enrichment (SPEC-0030).

Not a full pandoc: only the common agent idioms that otherwise pollute ideas.org.
"""
from __future__ import annotations

import re

# Inline code: `code` → ~code~  (skip already-tilde spans by converting backticks only)
_MD_CODE_RE = re.compile(r"`([^`\n]+)`")
# Bold: **x** or __x__ → *x*
_MD_BOLD_STAR_RE = re.compile(r"\*\*([^*\n]+)\*\*")
_MD_BOLD_UNDER_RE = re.compile(r"__([^_\n]+)__")
# ATX headings at line start
_ATX_RE = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+(.*)$")
# Fenced code blocks
_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

# Org → MD (promote Context): ~code~ / =verbatim= → `…`; *bold* → **bold**
_ORG_CODE_RE = re.compile(r"~([^~\n]+)~")
_ORG_VERBATIM_RE = re.compile(r"=([^=\n]+)=")
_ORG_BOLD_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_ORG_HEADLINE_RE = re.compile(r"^\*+\s")


def to_org_body(text: str) -> str:
    """Convert common Markdown idioms in enrichment prose to org-native markup."""
    if not text:
        return text
    text = _FENCE_RE.sub(lambda m: m.group(1).rstrip() + "\n", text)
    out_lines = []
    for line in text.splitlines(keepends=True):
        nl = ""
        if line.endswith("\n"):
            nl = "\n"
            core = line[:-1]
        else:
            core = line
        # Preserve trailing \r if any
        if core.endswith("\r"):
            core = core[:-1]
            # rare; drop CR
        m = _ATX_RE.match(core)
        if m:
            core = m.group(1)
        core = _MD_CODE_RE.sub(r"~\1~", core)
        core = _MD_BOLD_STAR_RE.sub(r"*\1*", core)
        core = _MD_BOLD_UNDER_RE.sub(r"*\1*", core)
        out_lines.append(core + nl)
    return "".join(out_lines)


def from_org_body(text: str) -> str:
    """Convert common org emphasis to Markdown for spec Context prefills.

    Org headlines (`*`, `**`, …) are left untouched so `** Summary` survives promote.
    """
    if not text:
        return text
    out = []
    for line in text.splitlines(keepends=True):
        nl = "\n" if line.endswith("\n") else ""
        core = line[:-1] if nl else line
        if _ORG_HEADLINE_RE.match(core):
            out.append(core + nl)
            continue
        core = _ORG_CODE_RE.sub(r"`\1`", core)
        core = _ORG_VERBATIM_RE.sub(r"`\1`", core)
        core = _ORG_BOLD_RE.sub(r"**\1**", core)
        out.append(core + nl)
    return "".join(out)
