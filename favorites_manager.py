import json
import os
from _constants import CACHE_DIR

_FILE = os.path.join(CACHE_DIR, "favorites.json")


class FavoritesManager:
    """Persists a set of (platform, rom_name) favorites to disk."""

    def __init__(self):
        self._favs: set[tuple[str, str]] = set()
        self._load()

    def toggle(self, platform: str, rom_name: str) -> bool:
        """Toggle favorite. Returns True if now favorited."""
        key = (platform, rom_name)
        if key in self._favs:
            self._favs.discard(key)
        else:
            self._favs.add(key)
        self._save()
        return key in self._favs

    def is_favorite(self, platform: str, rom_name: str) -> bool:
        return (platform, rom_name) in self._favs

    def all(self) -> list[tuple[str, str]]:
        return sorted(self._favs, key=lambda x: (x[0], x[1]))

    def count(self) -> int:
        return len(self._favs)

    def _save(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(_FILE, "w") as f:
            json.dump([list(item) for item in self._favs], f)

    def _load(self):
        try:
            with open(_FILE) as f:
                data = json.load(f)
            self._favs = {(row[0], row[1]) for row in data if len(row) == 2}
        except (FileNotFoundError, json.JSONDecodeError, TypeError, IndexError):
            self._favs = set()
