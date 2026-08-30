"""Tiny, dependency-light spec-markdown parsing: split YAML frontmatter from the body, and
map `## Heading` -> section text. Lives in the package (not tools/spec_lint.py) so the
installed `wt` never has to reach into the repo's dev tooling — which pulls in dev-only deps
like jsonschema — at runtime. `tools/spec_lint.py` keeps its own copies to stay standalone."""
import re

import yaml


def split_frontmatter(text):
    """(frontmatter_dict_or_None, body). A file without a `---`-delimited block -> (None, text)."""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text
    return yaml.safe_load(m.group(1)), m.group(2)


def sections(body):
    """Map '## Heading' -> section text (until the next '## ')."""
    out, cur, buf = {}, None, []
    for line in body.splitlines():
        h = re.match(r"^##\s+(.*?)\s*$", line)
        if h:
            if cur is not None:
                out[cur] = "\n".join(buf).strip()
            cur, buf = h.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf).strip()
    return out
