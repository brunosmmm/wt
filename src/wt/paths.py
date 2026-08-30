"""XDG base-directory resolution for wt's config, data, and cache locations.

Precedence per location (all paths expanduser'd):
  config: $WT_CONFIG_DIR, else $XDG_CONFIG_HOME/wt, else ~/.config/wt
  data:   $WT_DATA_DIR,   else $XDG_DATA_HOME/wt,   else ~/.local/share/wt
  cache:  $WT_CACHE_DIR,  else $XDG_CACHE_HOME/wt,  else ~/.cache/wt

A WT_*_DIR override is the full directory; an XDG_*_HOME base gets '/wt' appended.

  config dir -> config.yaml, mappings.yaml, overrides.yaml
  data dir   -> meetings.jsonl, history.jsonl, reports/, exports/
  cache dir  -> transient raw calendar dumps
"""
import os

APP = "wt"


def _resolve(direct_env, xdg_env, default_home_subdir):
    direct = os.environ.get(direct_env)
    if direct:
        return os.path.expanduser(direct)
    base = os.environ.get(xdg_env)
    if base:
        return os.path.join(os.path.expanduser(base), APP)
    return os.path.expanduser(os.path.join("~", default_home_subdir, APP))


def config_dir():
    return _resolve("WT_CONFIG_DIR", "XDG_CONFIG_HOME", ".config")


def data_dir():
    return _resolve("WT_DATA_DIR", "XDG_DATA_HOME", os.path.join(".local", "share"))


def cache_dir():
    return _resolve("WT_CACHE_DIR", "XDG_CACHE_HOME", ".cache")
