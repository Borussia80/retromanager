import json, os, pickle
from typing import Any, Tuple

# Helper
from _constants import *
from _debug import *



class SettingsHelper():
  def __init__(self):
    self.full_path = SETTINGS_FILE
    self._settings = {
      "cache_expiration": 30,
      "check_updates": False,
      "download_path": DEFAULT_DOWNLOAD_DIR,
      "unzip": True,
    }
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(self._settings["download_path"], exist_ok=True)
    if os.path.exists(self.full_path):
      self._read()
    else:
      DebugHelper.print(DebugType.TYPE_WARNING, f"<{SETTINGS_FILE}> not found.", "SETTINGS")
      self.write()


  def get(self, option: str):
    for op in self._settings:
      if option == op: return self._settings[option]
    raise ValueError(f"Setting <{option}> not found.")


  def update(self, option: Tuple[str, Any]):
    key, value = option

    for op in self._settings:
      if op == key:
        self._settings[key] = value
        DebugHelper.print(DebugType.TYPE_DEBUG, f"'{key}' updated to {value}.", "SETTINGS")
        return
    raise ValueError(f"Setting <{key}> not found.")


  def write(self):
    os.makedirs(os.path.dirname(self.full_path), exist_ok=True)
    with open(self.full_path, 'w', encoding='utf-8') as fp:
      json.dump(self._settings, fp, indent=2, sort_keys=True)
      fp.write("\n")
      DebugHelper.print(DebugType.TYPE_INFO, f"<{self.full_path}> wrote.", "SETTINGS")


  def _read(self):
    try:
      with open(self.full_path, 'r', encoding='utf-8') as fp:
        temp_settings: dict = json.load(fp)
        if len(temp_settings.keys()) != len(self._settings.keys()): self._fix(temp_settings)
        else: self._settings = temp_settings
        os.makedirs(self._settings["download_path"], exist_ok=True)
        DebugHelper.print(DebugType.TYPE_INFO, f"<{self.full_path}> loaded.", "SETTINGS")
        for option in self._settings: DebugHelper.print(DebugType.TYPE_DEBUG, f"'{option}': {str(self._settings[option])}")
    except EOFError: pass
    except json.JSONDecodeError:
      self._read_legacy_pickle()


  def _read_legacy_pickle(self):
    try:
      with open(self.full_path, 'rb') as fp:
        temp_settings: dict = pickle.load(fp)
      self._fix(temp_settings)
    except Exception as e:
      DebugHelper.print(DebugType.TYPE_ERROR, f"Could not read settings: {list(e.args)}", "SETTINGS")


  def _fix(self, old_settings: dict):
    DebugHelper.print(DebugType.TYPE_WARNING, f"Application and file mismatch. Trying to fix...", "SETTINGS")
    for key in old_settings:
      if key in self._settings:
        self._settings[key] = old_settings[key]
        DebugHelper.print(DebugType.TYPE_WARNING, f"'{key}' recovered.", "SETTINGS")
      else:
        DebugHelper.print(DebugType.TYPE_ERROR, f"'{key}' cannot be recovered.", "SETTINGS")
    self.write()
