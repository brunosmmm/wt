"""XDG path resolution + env override precedence (SPEC-0001)."""
import os

from wt import paths


def _clear(monkeypatch):
    for v in ("WT_CONFIG_DIR", "WT_DATA_DIR", "WT_CACHE_DIR",
              "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"):
        monkeypatch.delenv(v, raising=False)


def test_defaults(monkeypatch, tmp_path):
    _clear(monkeypatch)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert paths.config_dir() == str(tmp_path / ".config" / "wt")
    assert paths.data_dir() == str(tmp_path / ".local" / "share" / "wt")
    assert paths.cache_dir() == str(tmp_path / ".cache" / "wt")


def test_xdg_home_gets_wt_appended(monkeypatch, tmp_path):
    _clear(monkeypatch)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "dat"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cch"))
    assert paths.config_dir() == str(tmp_path / "cfg" / "wt")
    assert paths.data_dir() == str(tmp_path / "dat" / "wt")
    assert paths.cache_dir() == str(tmp_path / "cch" / "wt")


def test_wt_dir_is_used_verbatim_and_wins(monkeypatch, tmp_path):
    _clear(monkeypatch)
    # a direct WT_*_DIR override must win over XDG and be used as-is (no /wt appended)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "ignored"))
    monkeypatch.setenv("WT_CONFIG_DIR", str(tmp_path / "explicit"))
    assert paths.config_dir() == str(tmp_path / "explicit")


def test_tilde_expansion(monkeypatch, tmp_path):
    _clear(monkeypatch)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("WT_DATA_DIR", "~/somewhere")
    assert paths.data_dir() == str(tmp_path / "somewhere")
