import json
from pathlib import Path
from typing import TypedDict, cast

# Define the path to your config file
CONFIG_FILE_PATH = Path("playlists.json")


class PlaylistData(TypedDict):
    owner: str
    title: str
    total_tracks: int
    url: str
    id: str
    enabled: bool
    cover_url: str


class ConfigSchema(TypedDict):
    username: str
    playlists: dict[str, PlaylistData]


DEFAULT_CONFIG: ConfigSchema = {"username": "Spotify", "playlists": {}}


class ConfigManager:
    def __init__(self):
        self._data: ConfigSchema = self._load_config()

    def _load_config(self):
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                data = json.load(f)
                merged_config = cast(ConfigSchema, {**DEFAULT_CONFIG, **data})
                return merged_config
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

    # --- GETTERS ---

    def get_username(self):
        """Get the configured username"""
        return self._data.get("username", None)

    def get_all_playlists(self):
        """Get all saved playlists"""
        return self._data.get("playlists", None)

    def get_playlist(self, p_id: str):
        """Get a specific playlist with given id"""
        playlists = self.get_all_playlists()
        if playlists is None:
            return None
        return playlists.get(p_id)

    def get_all(self):
        """Return the entire config dictionary."""
        return self._data

    # --- SETTERS ---

    def set_username(self, new_username: str):
        """Set a new username value"""
        self._data["username"] = new_username
        self._save_config(self._data)

    def set_all_playlists(self, new_playlists: dict[str, PlaylistData]):
        """Set all playlists"""
        self._data["playlists"] = new_playlists
        self._save_config(self._data)

    def set_playlist(self, new_playlist: PlaylistData):
        """Set a specific playlist value"""
        if "playlists" not in self._data or self._data["playlists"] is None:
            self._data["playlists"] = {}
        self._data["playlists"][new_playlist.get("id")] = new_playlist
        self._save_config(self._data)


CONFIG = ConfigManager()
