# Qt
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

# Helpers
from _constants import *
from _platforms import PlatformsHelper
from _settings import SettingsHelper
from _debug import *


class CacheGenerator():
  class PlatformWorker(QObject):
    platform = []
    finished = pyqtSignal(str)


    def __init__(self, platform: list, output_cache_json: dict):
      super().__init__(None)
      self.platform = platform
      self.output_cache_json = output_cache_json


    def run(self):
      if len(self.platform) == 3: # SINGLE PART
        self.id_name = self.platform[0]
        self.format = self.platform[1]
        self.parts = 1
        self.url = f"https://archive.org/metadata/{self.platform[2]}"
        self.output_cache_json[self.id_name] = {}
        DebugHelper.print(DebugType.TYPE_DEBUG, f"Processing <{self.id_name}>", "CACHE")
        self._ProcessPart(part_id=self.platform[2])
      elif len(self.platform) == 4: # MULTI PART
        self.id_name = self.platform[0]
        self.format = self.platform[1]
        self.parts = self.platform[2]
        self.output_cache_json[self.id_name] = {}
        
        DebugHelper.print(DebugType.TYPE_DEBUG, f"Processing <{self.id_name}>", "CACHE")
        for i in range(1, self.parts+1):
          parts_id = str(self.platform[3]).replace('$$', str(i))
          self.url = f"https://archive.org/metadata/{parts_id}"
          self._ProcessPart(part_id=parts_id, part_number=i)
      self.finished.emit(self.id_name)


    def _ProcessPart(self, part_id: str, part_number: int = 1):
      import requests, json
      try:
        content_request = requests.get(self.url, timeout=30)
        content_request.raise_for_status()
        content_json = content_request.json()
        part_files = content_json.get('files', [])
        if not part_files:
          DebugHelper.print(DebugType.TYPE_WARNING, f"No files found for <{part_id}>. The Archive item may be private or unavailable.", "CACHE")
        for file_data in part_files:
          file = file_data.get('name', '')
          if file_data.get('format') == self.format and file.endswith(f".{self.format}"):
            output_file = {
              "source_id": part_id,
              "size": int(file_data.get('size', 0)),
              "md5": file_data.get('md5', ''),
              "crc32": file_data.get('crc32', ''),
              "sha1": file_data.get('sha1', ''),
              "format": file_data.get('format', self.format),
            }
            self.output_cache_json[self.id_name][file[:-(len(self.format)+1)]] = output_file
      except Exception as e:
        DebugHelper.print(DebugType.TYPE_ERROR, f"Could not fetch <{part_id}> from Archive: {e}", "CACHE")


  def __init__(self, app: QApplication, parent: QSplashScreen) -> None:
    self.app = app
    self.parent = parent
    self.output_cache_json = {}
    self.threads = []
    self.workers = []
    self.download_completed = 0
    self.event_loop = None


  def run(self):
    import json, os

    # Create workers and run them in separate threads (for speed)
    self.event_loop = QEventLoop()
    [self.threads.append(QThread()) for _ in range(len(ARCHIVE_PLATFORMS_DATA))]

    for i in range(len(ARCHIVE_PLATFORMS_DATA)):
      self.workers.append(CacheGenerator.PlatformWorker(ARCHIVE_PLATFORMS_DATA[i], self.output_cache_json))
      self.workers[i].moveToThread(self.threads[i])
      self.threads[i].started.connect(self.workers[i].run)
      self.workers[i].finished.connect(self._updateMessage)
      self.workers[i].finished.connect(self.threads[i].quit)
      self.threads[i].finished.connect(self.threads[i].deleteLater)
      self.threads[i].start()

    # Wait until workers finished without spinning the CPU.
    QTimer.singleShot(120000, self.event_loop.quit)
    if self.download_completed != len(self.threads):
      self.event_loop.exec()
    
    # Sort the data before writing
    self.output_cache_json = {name: self.output_cache_json[name] for name in sorted(self.output_cache_json)}
    
    # And finally write to file
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(PLATFORMS_CACHE_FILENAME, "w", encoding="utf-8") as fp:
      json.dump(self.output_cache_json, fp, indent=2, sort_keys=True)
      fp.write("\n")


  def _updateMessage(self, platform_name: str):
    self.download_completed += 1
    self.parent.showMessage(f"({self.download_completed}/{len(self.threads)}) [{platform_name}] completed.",
      color=Qt.GlobalColor.white,
      alignment=(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
    )
    if self.event_loop and self.download_completed == len(self.threads):
      self.event_loop.quit()



class DownloadWorker(QObject):
  startedItem = pyqtSignal(str, str, int, int)
  progress = pyqtSignal(int, int, float)
  completedItem = pyqtSignal(str, str)
  failedItem = pyqtSignal(str, str, str)
  cancelled = pyqtSignal()
  finished = pyqtSignal()


  def __init__(self, settings: SettingsHelper, platforms: PlatformsHelper, queue_items: list[tuple[str, str]]):
    super().__init__(None)
    self.settings = settings
    self.platforms = platforms
    self.queue_items = queue_items
    self._cancel_requested = False


  def cancel(self):
    self._cancel_requested = True


  def run(self):
    for current_index, (platform, rom_name) in enumerate(self.queue_items, start=1):
      if self._cancel_requested:
        self.cancelled.emit()
        break
      self.startedItem.emit(platform, rom_name, current_index, len(self.queue_items))
      try:
        output_path = self._download(platform, rom_name)
        if self.settings.get('unzip'):
          self._unzip(output_path)
        self.completedItem.emit(platform, rom_name)
      except Exception as e:
        self.failedItem.emit(platform, rom_name, str(e))
        break
    self.finished.emit()


  def _download(self, platform: str, rom_name: str) -> str:
    import hashlib, os, requests, time, zlib
    from urllib.parse import quote

    rom_data = self.platforms.getRom(platform, rom_name)
    rom_format = rom_data['format']
    rom_url = f"https://archive.org/download/{rom_data['source_id']}/{quote(rom_name)}.{rom_format}"
    output_path = os.path.join(self.settings.get('download_path'), f"{rom_name}.{rom_format}")
    temp_path = f"{output_path}.part"

    os.makedirs(self.settings.get('download_path'), exist_ok=True)
    if os.path.exists(temp_path):
      os.remove(temp_path)

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    crc32 = 0
    bytes_done = 0
    started_at = time.monotonic()

    try:
      DebugHelper.print(DebugType.TYPE_INFO, f"Downloading [{platform}] {rom_name}", "downloader")
      DebugHelper.print(DebugType.TYPE_DEBUG, f"Downloading from [{rom_url}]", "downloader")
      with requests.get(rom_url, timeout=60, stream=True) as response:
        response.raise_for_status()
        total_bytes = int(response.headers.get("content-length") or rom_data.get("size") or 0)
        with open(temp_path, "wb") as of:
          for chunk in response.iter_content(chunk_size=1024 * 64):
            if not chunk:
              continue
            if self._cancel_requested:
              raise InterruptedError("Download cancelled by user")
            of.write(chunk)
            md5.update(chunk)
            sha1.update(chunk)
            crc32 = zlib.crc32(chunk, crc32)
            bytes_done += len(chunk)
            elapsed = max(time.monotonic() - started_at, 0.001)
            self.progress.emit(bytes_done, total_bytes, bytes_done / elapsed)

      self._validateHash("MD5", md5.hexdigest(), rom_data.get("md5", ""))
      self._validateHash("SHA1", sha1.hexdigest(), rom_data.get("sha1", ""))
      self._validateHash("CRC32", f"{crc32 & 0xffffffff:08x}", rom_data.get("crc32", ""))
      os.replace(temp_path, output_path)
      return output_path
    except Exception:
      if os.path.exists(temp_path):
        os.remove(temp_path)
      raise


  def _validateHash(self, label: str, actual: str, expected: str):
    if expected and actual.lower() != expected.lower():
      raise ValueError(f"{label} mismatch: expected {expected}, got {actual}")


  def _unzip(self, archive_path: str):
    import os
    from py7zr import SevenZipFile

    path = self.settings.get('download_path')
    DebugHelper.print(DebugType.TYPE_INFO, f"Unzipping [{archive_path}]...", "unzip")
    with SevenZipFile(archive_path) as archive:
      archive.extractall(path)
    os.remove(archive_path)




class Tools():
  def convertSizeToReadable(size: int) -> str:
    if size < 1000:
      return '%i' % size + 'B'
    elif 1000 <= size < 1000000:
      return '%.1f' % float(size/1000) + ' KB'
    elif 1000000 <= size < 1000000000:
      return '%.1f' % float(size/1000000) + ' MB'
    elif 1000000000 <= size < 1000000000000:
      return '%.1f' % float(size/1000000000) + ' GB'
    elif 1000000000000 <= size:
      return '%.1f' % float(size/1000000000000) + ' TB'


  def isCacheValid(validity_days: int) -> bool:
    import os
    from datetime import datetime, timedelta

    if validity_days == 0:
      return True
    if not os.path.exists(PLATFORMS_CACHE_FILENAME):
      return False

    cache_mdate = os.path.getmtime(PLATFORMS_CACHE_FILENAME)
    cache_mdate = datetime.fromtimestamp(cache_mdate)
    today_date = datetime.today()
    expiration_date = cache_mdate + timedelta(days=validity_days)

    if expiration_date > today_date: return True
    else: return False
