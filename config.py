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


def read_config():
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
    """Returns the value with the given key from CONFIG_PATH, or default if the key does not exist"""
    return read_config().get(key)


def set_config_value(key: str, value):
    """
    Sets the given key to the given value in CONFIG_PATH
    :param key: str, key to set in CONFIG_PATH
    :param value: str, value to be matched with the given key
    """
    data = read_config()
    data[key] = value
    _write_config(data)

