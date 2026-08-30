"""What a REAL terminal renders (SPEC-0115).

Every desk defect the human reported got past headless pilots. The reason is structural: Textual
repaints *incrementally*, so raw pty bytes cannot be turned back into a screen by picking a frame
— you need a terminal emulator to apply the updates. `pyte` is that emulator.

This is deliberately one slow test rather than a suite: it spawns `wt tui` under a pty against a
throwaway org, and asserts on the composited screen.
"""
import os
import re
import shutil
import sys
import time
from pathlib import Path

import pytest

from wt import tui as T

pyte = pytest.importorskip("pyte", reason="pyte (dev dep) not installed")
pytestmark = pytest.mark.skipif(
    not T.textual_available() or not hasattr(os, "forkpty"),
    reason="needs the tui extra and a POSIX pty",
)

COLS, ROWS = 110, 30


def _throwaway_org(tmp_path):
    """A config dir + org file with an epic, two children, a loose idea and a project-less one."""
    conf, org = tmp_path / "config", tmp_path / "org"
    conf.mkdir(), org.mkdir()
    (conf / "config.yaml").write_text(
        f'org_files: ["{org}"]\n'
        f"org_ideas_file: {org}/ideas.org\n"
        f"org_capture_file: {org}/inbox.org\n"
        f"specs_dir: {tmp_path}/specs\n"
        "project_axis: bucket\n")
    (conf / "mappings.yaml").write_text("a:\n  bucket: Alpha\n")
    specs = tmp_path / "specs"
    specs.mkdir()
    for num, extra in ((1, "kind: epic\n"), (2, "kind: feature\nparent: SPEC-0001\n")):
        (specs / f"{num:04d}-x.md").write_text(
            f"---\nid: SPEC-{num:04d}\ntitle: \"s{num}\"\nstatus: accepted\nowner: b\n"
            f"created: 2026-07-31\nupdated: 2026-07-31\n{extra}---\n\n## Context\n\nx\n")
    (org / "ideas.org").write_text(
        "#+TODO: IDEA INCUBATE SPECCED | PROMOTED EXPORTED DROPPED RESEARCHED\n\n"
        # :UPDATED: stamps make the order deterministic. Without them freshness ties and falls
        # back to the heading, so the epic sorted *after* the loose idea and the cursor landed on
        # a leaf — the test then "proved" Enter did not expand.
        "* SPECCED the parent epic idea\n"
        "  :PROPERTIES:\n  :ID: IDEA-001\n  :PROJECT: Alpha\n  :SPEC: SPEC-0001\n"
        "  :UPDATED: [2026-07-31 Fri 12:00]\n  :END:\n"
        "* SPECCED the nested child idea\n"
        "  :PROPERTIES:\n  :ID: IDEA-002\n  :PROJECT: Alpha\n  :SPEC: SPEC-0002\n"
        "  :UPDATED: [2026-07-31 Fri 11:00]\n  :END:\n"
        "* IDEA a loose alpha idea\n"
        "  :PROPERTIES:\n  :ID: IDEA-003\n  :PROJECT: Alpha\n"
        "  :UPDATED: [2026-07-30 Thu 09:00]\n  :END:\n")
    return conf


def _render(conf_dir, keys, *, settle=6.0, per_key=1.6):
    """Spawn `wt tui` under a pty and return the composited screen as lines."""
    import fcntl
    import pty
    import select
    import struct
    import termios

    pid, fd = pty.fork()
    if pid == 0:                                            # child
        os.environ.update(TERM="xterm-256color", COLUMNS=str(COLS), LINES=str(ROWS),
                          WT_CONFIG_DIR=str(conf_dir), WT_DATA_DIR=str(conf_dir))
        os.execvp(sys.executable, [sys.executable, "-m", "wt.cli", "tui"])
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))

    screen = pyte.Screen(COLS, ROWS)
    stream = pyte.ByteStream(screen)

    def pump(seconds):
        end = time.time() + seconds
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.1)
            if r:
                try:
                    data = os.read(fd, 1 << 20)
                except OSError:
                    return
                if not data:
                    return
                stream.feed(data)

    def cells():
        """Per-cell (char, fg) so a test can assert on **colour**, not just text."""
        return [[(screen.buffer[y][x].data, screen.buffer[y][x].fg) for x in range(COLS)]
                for y in range(ROWS)]

    try:
        pump(settle)
        for key in keys:
            named = {"ENTER": b"\r", "ESC": b"\x1b", "SPACE": b" ", "TAB": b"\t"}
            if len(key) > 1 and key not in named:
                raise AssertionError(f"unknown key name {key!r} — it would be typed literally")
            os.write(fd, named.get(key, key.encode()))
            pump(per_key)
        return [line.rstrip() for line in screen.display], cells()
    finally:
        try:
            os.write(fd, b"q")
            pump(0.6)
            os.close(fd)
        except OSError:
            pass
        try:
            os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            pass


def test_tree_mode_renders_real_nesting_in_a_real_terminal(tmp_path):
    """The check that would have caught the shipped SPEC-0114 desk mode.

    Asserts on the composited screen: a disclosure marker on the project, the epic present with
    its own marker, and — once expanded — the child indented further than its parent.
    """
    conf = _throwaway_org(tmp_path)
    if shutil.which("uv") is None and not Path(sys.executable).exists():
        pytest.skip("no interpreter to spawn")

    flat = "\n".join(_render(conf, [])[0])
    assert "IDEA-001" in flat, f"desk did not render any ideas:\n{flat}"
    assert "▼" not in flat and "▶" not in flat, "flat view should have no disclosure markers"

    lines, _cells = _render(conf, ["g"])
    screen = "\n".join(lines)
    assert "Alpha" in screen, f"no project group:\n{screen}"
    assert "▼" in screen or "▶" in screen, f"no disclosure markers — not a tree:\n{screen}"
    assert "IDEA-001" in screen

    def column_of(needle):
        """Column where `needle` starts. Textual draws nesting with guide glyphs (`├──`), not
        leading whitespace, so `lstrip()` would report 0 for every depth."""
        for line in lines:
            if needle in line:
                return line.index(needle)
        return None

    project_indent = column_of("Alpha")
    epic_indent = column_of("IDEA-001")
    assert project_indent is not None and epic_indent is not None
    assert epic_indent > project_indent, (
        f"epic not indented under its project ({epic_indent} vs {project_indent}):\n{screen}")

    # expand the epic: cursor starts on the first idea, so Enter toggles it
    expanded = "\n".join(_render(conf, ["g", "ENTER"])[0])
    assert "IDEA-002" in expanded, f"expanding the epic revealed no child:\n{expanded}"


def test_tree_is_not_monochrome(tmp_path):
    """Reported: "in tree view there is no color at all".

    The first tree implementation styled node labels `dim` or not at all, discarding SPEC-0082's
    state hue, SPEC-0085's kind glyph and SPEC-0110's yellow question count. Asserts on the
    colours a real terminal actually paints, and that distinct states get distinct hues — a count
    alone would pass on a tree that coloured everything the same.
    """
    conf = _throwaway_org(tmp_path)
    org = conf.parent / "org" / "ideas.org"
    org.write_text(org.read_text() +
                   "* INCUBATE has questions\n  :PROPERTIES:\n  :ID: IDEA-004\n"
                   "  :PROJECT: Alpha\n  :UPDATED: [2026-07-31 Fri 10:00]\n  :END:\n"
                   "** Open questions\n*** OPEN why?\n"
                   "* DROPPED a dead one\n  :PROPERTIES:\n  :ID: IDEA-005\n"
                   "  :PROJECT: Alpha\n  :UPDATED: [2026-07-31 Fri 09:00]\n  :END:\n")

    tree_lines, tree_cells = _render(conf, ["a", "g"])

    def pane_width(lines):
        """Column of the pane divider. Everything right of it is the *detail* pane, which
        SPEC-0107 lexes in colour — measuring the whole screen made this test vacuous: it passed
        on a monochrome tree because the detail pane supplied the colours."""
        for line in lines:
            if "│" in line:
                return line.index("│")
        return len(max(lines, key=len))

    def palette(cells, lines):
        limit = pane_width(lines)
        return {fg for row in cells for ch, fg in row[:limit] if ch.strip()}

    def colour_of(cells, lines, word):
        """The fg of `word`'s first character, searched in the **left pane only**."""
        limit = pane_width(lines)
        for y, line in enumerate(lines):
            head = line[:limit]
            if word in head:
                return cells[y][head.index(word)][1]
        return None

    # Assertions deliberately avoid counting colours: even a monochrome tree shows ~10 in this
    # pane, from the tab bar, tree guides and footer keys. They also avoid the *cursor* row, whose
    # highlight colour would make any state look distinct. Comparing two NON-cursor rows is what
    # actually discriminates — an earlier version of this test passed on the monochrome build.
    incubate = colour_of(tree_cells, tree_lines, "INCUBATE")
    dropped = colour_of(tree_cells, tree_lines, "DROPPED")
    heading = colour_of(tree_cells, tree_lines, "has questions")
    assert incubate and dropped and heading

    # SPEC-0082: the state hue encodes which way an idea closed, so two different states must not
    # render identically, and a state must not render as plain body text.
    assert incubate != dropped, f"states share one colour: {incubate}"
    assert incubate != heading, f"state is not coloured: {incubate} == body {heading}"

    # SPEC-0110: the open-question count is its own colour, not the heading's.
    q_colour = colour_of(tree_cells, tree_lines, "1q")
    assert q_colour and q_colour != heading, f"question count not coloured: {q_colour}"
