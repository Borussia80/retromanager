import json, os, pickle

# Helpers
from _constants import *
from _debug import *


class PlatformsHelper():
  def __init__(self):
    self._platformsCache = {}
    if os.path.exists(PLATFORMS_CACHE_FILENAME):
      try:
        with open(PLATFORMS_CACHE_FILENAME, 'r', encoding='utf-8') as fp:
          data = json.load(fp)
        if not isinstance(data, dict) or not all(isinstance(v, dict) for v in data.values()):
          raise ValueError("Cache structure invalid")
        self._platformsCache = data
        DebugHelper.print(DebugType.TYPE_INFO, f"<{PLATFORMS_CACHE_FILENAME}> sucessfully loaded!", "PLATFORMS")
      except json.JSONDecodeError:
        self._read_legacy_pickle()
      except ValueError as e:
        DebugHelper.print(DebugType.TYPE_ERROR, f"Cache inválido, ignorando: {e}", "PLATFORMS")
        self._try_delete_bad_cache()
      except OSError as e:
        DebugHelper.print(DebugType.TYPE_ERROR, f"Error: {list(e.args)}", "PLATFORMS")


  def _read_legacy_pickle(self):
    try:
      with open(PLATFORMS_CACHE_FILENAME, 'rb') as fp:
        self._platformsCache = pickle.load(fp)
      DebugHelper.print(DebugType.TYPE_INFO, f"<{PLATFORMS_CACHE_FILENAME}> legacy cache loaded!", "PLATFORMS")
    except (pickle.UnpicklingError, OSError, EOFError, AttributeError) as e:
      DebugHelper.print(DebugType.TYPE_ERROR, f"Error: {list(e.args)}", "PLATFORMS")
      self._try_delete_bad_cache()

  def _try_delete_bad_cache(self):
    try:
      os.remove(PLATFORMS_CACHE_FILENAME)
      DebugHelper.print(DebugType.TYPE_WARNING, "Cache corrompido removido.", "PLATFORMS")
    except OSError:
      pass

  
  def platformsCount(self) -> int:
    return len(self._platformsCache)
  
  
  def getRomsCount(self, platform_name: str) -> int:
    return len(self._platformsCache[platform_name])


  def getPlatformName(self, index: int) -> str:
    return list(self._platformsCache.keys())[index]


  def getPlatforms(self):
    return self._platformsCache.keys()
  

  def getRomName(self, platform_name: str, index: int) -> str:
    return list(self._platformsCache[platform_name].keys())[index]


  def getRom(self, platform_name: str, rom_name: str) -> dict | None:
    try:
      return self._platformsCache[platform_name][rom_name]
    except KeyError:
      return None


  def getRoms(self, platform_name: str):
    return self._platformsCache[platform_name].items()
