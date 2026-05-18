"""
MAME shortname → friendly title cache.

Cache file: ~/.cache/retromanager/mame_names.json
Source XML:  looked up from several well-known locations (see SEARCH_PATHS).
             The user can also place mame.xml directly in the cache dir.

Parsing uses iterparse so the full XML (~350 MB) is never held in memory.
"""

import json
import logging
import os
import xml.etree.ElementTree as ET
from _constants import MAME_NAMES_CACHE, CACHE_DIR

_log = logging.getLogger("retromanager.mame_names")

SEARCH_PATHS = [
    os.path.join(CACHE_DIR, "mame.xml"),
    os.path.expanduser("~/.mame/mame.xml"),
    "/usr/share/mame/mame.xml",
    "/usr/share/games/mame/mame.xml",
    "/usr/local/share/mame/mame.xml",
]


def _find_xml() -> str | None:
    for p in SEARCH_PATHS:
        if os.path.isfile(p):
            return p
    return None


def _parse_xml(xml_path: str) -> dict[str, str]:
    """Parse mame.xml and return {shortname: friendly_title}."""
    names: dict[str, str] = {}
    for event, elem in ET.iterparse(xml_path, events=("end",)):
        if elem.tag == "machine":
            shortname = elem.get("name", "")
            desc_el = elem.find("description")
            if shortname and desc_el is not None and desc_el.text:
                names[shortname] = desc_el.text
            elem.clear()
    return names


def _save(names: dict[str, str]) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(MAME_NAMES_CACHE, "w", encoding="utf-8") as f:
        json.dump(names, f, ensure_ascii=False, separators=(",", ":"))


def load() -> dict[str, str]:
    """
    Return cached {shortname: title} dict.
    Returns empty dict if no cache and no XML source found.
    """
    if os.path.isfile(MAME_NAMES_CACHE):
        try:
            with open(MAME_NAMES_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    xml_path = _find_xml()
    if not xml_path:
        return {}

    try:
        names = _parse_xml(xml_path)
        _save(names)
        return names
    except (ET.ParseError, OSError) as e:
        _log.warning("failed to parse MAME XML at %s: %s", xml_path, e)
        return {}


def xml_available() -> bool:
    return bool(_find_xml())


def cache_available() -> bool:
    return os.path.isfile(MAME_NAMES_CACHE)
