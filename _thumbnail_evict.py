"""LRU eviction for the on-disk thumbnail cache — no Qt dependency."""
import os

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "retromanager", "thumbnails")

MAX_CACHE_BYTES = 200 * 1024 * 1024   # 200 MB
MAX_CACHE_COUNT = 5_000               # 5 000 thumbnails


def evict_lru(cache_dir: str = CACHE_DIR,
              max_bytes: int = MAX_CACHE_BYTES,
              max_count: int = MAX_CACHE_COUNT) -> int:
    """Remove oldest thumbnails (by mtime) until cache is within limits.

    Returns the number of files deleted.
    """
    entries: list[tuple[float, int, str]] = []  # (mtime, size, path)
    for dirpath, _, filenames in os.walk(cache_dir):
        for fname in filenames:
            if not fname.endswith(".png"):
                continue
            full = os.path.join(dirpath, fname)
            try:
                st = os.stat(full)
                entries.append((st.st_mtime, st.st_size, full))
            except OSError:
                pass

    total_bytes = sum(e[1] for e in entries)
    total_count = len(entries)

    if total_bytes <= max_bytes and total_count <= max_count:
        return 0

    entries.sort()  # oldest mtime first
    deleted = 0
    for _, size, path in entries:
        if total_bytes <= max_bytes and total_count <= max_count:
            break
        try:
            os.remove(path)
            total_bytes -= size
            total_count -= 1
            deleted += 1
        except OSError:
            pass
    return deleted
