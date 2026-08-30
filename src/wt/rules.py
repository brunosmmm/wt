"""The human-owned rules layer: mappings.yaml (base topic -> facets) and overrides.yaml
(session + time range -> topic). Read at report time; the parser never writes these."""
import os
import sys
from pathlib import Path

import yaml

from .config import _load_yaml
from .dates import _parse_iso


def _mappings_path(cfg):
    return os.path.join(cfg["config_dir"], "mappings.yaml")


def _overrides_path(cfg):
    return os.path.join(cfg["config_dir"], "overrides.yaml")


def load_mappings(cfg):
    """base topic -> {axis: value} facets. A bare string is shorthand for {bucket: str}."""
    raw = _load_yaml(_mappings_path(cfg), {}) or {}
    return {k: ({"bucket": v} if isinstance(v, str) else dict(v or {})) for k, v in raw.items()}


def resolve_facets(cfg, topic, mappings=None) -> dict:
    """Effective facets for a base topic (SPEC-0027).

    Exact mapping wins; otherwise inherit from the prefix before the first `:`, if that
    parent key is mapped. Returns a shallow copy (never the live mappings entry).
    """
    m = mappings if mappings is not None else load_mappings(cfg)
    if topic in m:
        return dict(m[topic])
    if ":" in topic:
        parent = topic.split(":", 1)[0]
        if parent and parent != topic and parent in m:
            return dict(m[parent])
    return {}


def known_projects(cfg):
    """Sorted distinct values of cfg['project_axis'] (default 'bucket') across
    load_mappings(cfg) — the de-facto project registry (SPEC-0018)."""
    axis = cfg.get("project_axis", "bucket")
    values = {facets[axis] for facets in load_mappings(cfg).values() if axis in facets}
    return sorted(values)


def projects_payload(cfg) -> dict:
    """Agent-facing project map for `wt projects --json` (SPEC-0095).

    Union of mapping buckets, `outbox_targets` keys, and Meta-Tools — each with topic count,
    outbound flag, and `resolve_research_context` (never invents paths).
    """
    axis = cfg.get("project_axis", "bucket")
    counts = {}
    for facets in load_mappings(cfg).values():
        val = facets.get(axis)
        if val:
            counts[val] = counts.get(val, 0) + 1
    outbox = cfg.get("outbox_targets") or {}
    names = set(known_projects(cfg)) | set(outbox.keys()) | {"Meta-Tools"}
    projects = []
    for name in sorted(names):
        projects.append({
            "name": name,
            "topics": counts.get(name, 0),
            "outbound": name in outbox,
            "research": resolve_research_context(cfg, name),
        })
    return {"schema": "wt.projects.v1", "projects": projects}


def discover_wt_checkout():
    """Filesystem root of this wt tooling repo (SPEC-0042 Meta-Tools research root).

    Walks from the installed `wt` package upward looking for `src/wt` + `pyproject.toml`.
    Returns an absolute path string, or None if not found (e.g. bare wheel without repo).
    """
    import wt as _wt
    here = Path(_wt.__file__).resolve().parent
    for cand in [here, *here.parents]:
        if (cand / "src" / "wt").is_dir() and (cand / "pyproject.toml").is_file():
            return str(cand)
    return None


def resolve_research_context(cfg, project=None):
    """Where agents should search code for an idea's :PROJECT: (SPEC-0042).

    Returns a dict: root (expanded path or None), source
    ('outbox_targets' | 'internal' | 'none'), optional spec_dir/scheme, optional note.
    Never invents paths from mappings.yaml or ~/work/<slug>.
    """
    project = (project or "").strip() or None
    outbox = cfg.get("outbox_targets") or {}

    if project and project in outbox:
        target = outbox.get(project) or {}
        raw = (target.get("repo_path") or "").strip()
        root = os.path.expanduser(raw) if raw else None
        ctx = {"root": root, "source": "outbox_targets"}
        if target.get("spec_dir"):
            ctx["spec_dir"] = target["spec_dir"]
        if target.get("scheme"):
            ctx["scheme"] = target["scheme"]
        if not root:
            ctx["note"] = f"outbox_targets[{project!r}] has empty repo_path"
        return ctx

    if project == "Meta-Tools":
        root = discover_wt_checkout()
        if root:
            return {"root": root, "source": "internal"}
        return {
            "root": None,
            "source": "none",
            "note": "could not discover wt checkout for internal Meta-Tools",
        }

    if project:
        return {
            "root": None,
            "source": "none",
            "note": (
                f"project {project!r} has no outbox_targets.repo_path; "
                "configure it for explore routing (or explore without a tree)"
            ),
        }

    return {
        "root": None,
        "source": "none",
        "note": "no :PROJECT:; explore from conversation only",
    }


def load_overrides(cfg):
    raw = _load_yaml(_overrides_path(cfg), []) or []
    out = []
    for ov in raw:
        try:
            out.append({
                "session": ov["session"],
                "_start": _parse_iso(ov["start"]),
                "_end": _parse_iso(ov["end"]),
                "topic": ov["topic"],
                "note": ov.get("note", ""),
            })
        except Exception as e:
            print(f"  ! skipping bad override {ov!r}: {e}", file=sys.stderr)
    return out


def set_facets(cfg, raw, facets):
    """Merge {axis: value} facets into a base topic's mapping entry."""
    path = _mappings_path(cfg)
    raw_map = _load_yaml(path, {}) or {}
    cur = raw_map.get(raw)
    cur = {"bucket": cur} if isinstance(cur, str) else dict(cur or {})
    cur.update(facets)
    raw_map[raw] = cur
    with open(path, "w") as f:
        yaml.safe_dump(raw_map, f, sort_keys=True, default_flow_style=False)


def add_override_rec(cfg, session, start, end, topic, note=""):
    path = _overrides_path(cfg)
    lst = _load_yaml(path, []) or []
    lst.append({"session": session, "start": start, "end": end, "topic": topic, "note": note or ""})
    with open(path, "w") as f:
        yaml.safe_dump(lst, f, sort_keys=False, default_flow_style=False)
