import json
from pathlib import Path

# Define the path to your config file
CONFIG_FILE_PATH = Path("playlists.json")
DEFAULT_CONFIG = {"username": "Spotify", "playlists": []}


class ConfigManager:
    def __init__(self):
        self._data = self._load_config()

    def _load_config(self):
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except (FileNotFoundError, json.JSONDecodeError):
            print(
                f"Config file not found or invalid. Creating default config at {CONFIG_FILE_PATH}"
            )
            self._save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG

    def _save_config(self, data):
        try:
            with open(CONFIG_FILE_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving config file: {e}")

    def get(self, key, default=None):
        """Get a configuration value."""
        return self._data.get(key, default)

    def set(self, key, value):
        """Set a configuration value and save the changes."""
        self._data[key] = value
        self._save_config(self._data)

    def get_all(self):
        """Return the entire config dictionary."""
        return self._data


CONFIG = ConfigManager()
