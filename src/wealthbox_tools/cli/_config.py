from __future__ import annotations

import json
import os
import pathlib
import platform
from typing import Any


def _config_dir() -> pathlib.Path:
    """Return the platform-appropriate config directory for wbox."""
    if platform.system() == "Windows":
        base = pathlib.Path(os.environ.get("APPDATA", "~"))
    else:
        base = pathlib.Path(os.environ.get("XDG_CONFIG_HOME", "~/.config"))
    return base.expanduser() / "wbox"


def _config_path() -> pathlib.Path:
    return _config_dir() / "config.json"


def _user_dir() -> pathlib.Path:
    """Return the L3 user-preferences directory (sibling of the firm dir).

    Always returns an absolute path: ``_config_dir()`` honours
    ``XDG_CONFIG_HOME`` / ``APPDATA`` verbatim, which can be set to a
    relative value. The ``prefs path`` / helper contract guarantees an
    absolute result regardless of the caller's current working directory,
    so we resolve here. (``_config_dir()`` itself is intentionally left
    alone — it has many existing consumers and changing its semantics is
    out of scope for the prefs slot.)
    """
    return (_config_dir() / "user").resolve()


def _user_prefs_path() -> pathlib.Path:
    """Return the absolute path to the user's ``preferences.md`` file.

    The file may be empty or absent — callers must not assume it exists.
    The directory is hand-edited; ``wbox`` never writes to it implicitly.
    Absolute-ness is inherited from ``_user_dir()``.
    """
    return _user_dir() / "preferences.md"


def load_config() -> dict[str, Any]:
    """Load config from disk. Returns empty dict if file doesn't exist."""
    path = _config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save config to disk. Creates directory if needed."""
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n")
    if platform.system() != "Windows":
        path.chmod(0o600)


def get_stored_token() -> str | None:
    """Get token from config file, or None if not set."""
    return load_config().get("token")
