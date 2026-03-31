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


def get_stored_token() -> str | None:
    """Get token from config file, or None if not set."""
    return load_config().get("token")
