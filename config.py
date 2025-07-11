import json
import os
import platform
from pathlib import Path


def get_appdata_path():
    """Return platform appropriate path for storing config files"""
    system = platform.system()
    if system == "Windows":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    return base / "testvault-alerts"


CONFIG_PATH = get_appdata_path() / "config.json"


def _read_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_config(data: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f)


def get_config_value(key: str):
    return _read_config().get(key)


def set_config_value(key: str, value):
    data = _read_config()
    data[key] = value
    _write_config(data)

