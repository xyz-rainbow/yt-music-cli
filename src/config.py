
import os
from pathlib import Path

APP_NAME = "yt-music-cli"

def get_config_dir() -> Path:
    """Returns the configuration directory for the application."""
    config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_dir = Path(config_home) / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_data_dir() -> Path:
    """Returns the data directory for the application (logs, cache, etc)."""
    data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    data_dir = Path(data_home) / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
