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
    finished = pyqtSignal(str)


    def __init__(self, platform: list, output_cache_json: dict):
      super().__init__(None)
      self.platform = platform
      self.output_cache_json = output_cache_json


    def run(self):
      self.id_name = self.platform[0]
      self.format = self.platform[1].lower()
      source = self.platform[2]
      self.output_cache_json[self.id_name] = {}
      DebugHelper.print(DebugType.TYPE_DEBUG, f"Processing <{self.id_name}>", "CACHE")

      if isinstance(source, list):
        for part_id in source:
          self._ProcessPart(part_id)
      else:
        self._ProcessPart(source)

      self.finished.emit(self.id_name)


    def _ProcessPart(self, part_id: str):
      import os, requests
      url = f"https://archive.org/metadata/{part_id}"
      try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        part_files = response.json().get('files', [])
        if not part_files:
          DebugHelper.print(DebugType.TYPE_WARNING, f"No files found for <{part_id}>. The Archive item may be private or unavailable.", "CACHE")
        for file_data in part_files:
          file_path = file_data.get('name', '')
          file_basename = os.path.basename(file_path)
          if file_data.get('format', '').lower() == self.format and file_basename.lower().endswith(f".{self.format}"):
            rom_key = file_basename[:-(len(self.format) + 1)]
            self.output_cache_json[self.id_name][rom_key] = {
              "source_id": part_id,
              "file_path": file_path,
              "size": int(file_data.get('size', 0)),
              "md5": file_data.get('md5', ''),
              "crc32": file_data.get('crc32', ''),
              "sha1": file_data.get('sha1', ''),
              "format": self.format,
            }
      except (requests.exceptions.RequestException, ValueError, KeyError, OSError) as e:
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
      except InterruptedError:
        self.cancelled.emit()
        break
      except PermissionError as e:
        msg = f"Permissão negada: {e.filename or rom_name}"
        self.failedItem.emit(platform, rom_name, msg)
        break
      except OSError as e:
        import errno as _errno
        if e.errno == _errno.ENOSPC:
          msg = "Disco cheio — libere espaço e tente novamente."
        else:
          msg = str(e)
        self.failedItem.emit(platform, rom_name, msg)
        break
      except Exception as e:
        self.failedItem.emit(platform, rom_name, str(e))
        break
    self.finished.emit()


  def _download(self, platform: str, rom_name: str) -> str:
    import hashlib, os, requests, time, zlib
    from urllib.parse import quote

    rom_data = self.platforms.getRom(platform, rom_name)
    if not rom_data:
      raise ValueError(f"ROM não encontrada no catálogo: {rom_name}")
    rom_format = rom_data['format']
    source_id = rom_data.get('source_id', '')
    import re as _re
    if not _re.fullmatch(r'[\w][\w.\-]*', source_id):
      raise ValueError(f"source_id inválido no catálogo: {source_id!r}")
    file_path = rom_data.get('file_path')
    encoded_path = quote(file_path, safe='/') if file_path else f"{quote(rom_name)}.{rom_format}"
    rom_url = f"https://archive.org/download/{source_id}/{encoded_path}"
    if not rom_url.startswith("https://archive.org/"):
      raise ValueError(f"URL de download fora do domínio permitido: {rom_url}")

    base_dir = self.settings.get('download_path')
    output_dir = os.path.join(base_dir, platform) if self.settings.get('organize_by_platform') else base_dir
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"{rom_name}.{rom_format}")
    temp_path   = f"{output_path}.part"

    # Resume from partial file if present
    resume_from = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    crc32 = 0
    bytes_done = resume_from
    started_at = time.monotonic()

    if resume_from > 0:
      DebugHelper.print(DebugType.TYPE_INFO, f"Resuming [{platform}] {rom_name} from {resume_from}B", "downloader")
      with open(temp_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
          md5.update(chunk)
          sha1.update(chunk)
          crc32 = zlib.crc32(chunk, crc32)

    headers = {'Range': f'bytes={resume_from}-'} if resume_from > 0 else {}

    try:
      DebugHelper.print(DebugType.TYPE_INFO, f"Downloading [{platform}] {rom_name}", "downloader")
      DebugHelper.print(DebugType.TYPE_DEBUG, f"URL: {rom_url}", "downloader")

      with requests.get(rom_url, timeout=60, stream=True, headers=headers) as resp:
        # Server returned 200 instead of 206 → doesn't support Range; restart fresh
        if resume_from > 0 and resp.status_code == 200:
          resume_from = 0
          bytes_done  = 0
          md5, sha1, crc32 = hashlib.md5(), hashlib.sha1(), 0
        else:
          resp.raise_for_status()

        total_bytes = int(resp.headers.get("content-length") or rom_data.get("size") or 0)
        if resume_from > 0:
          total_bytes += resume_from

        open_mode = "ab" if resume_from > 0 else "wb"
        with open(temp_path, open_mode) as of:
          for chunk in resp.iter_content(chunk_size=65536):
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

      # Validate — hash mismatch: delete corrupt .part
      try:
        self._validateHash("MD5",   md5.hexdigest(),              rom_data.get("md5", ""))
        self._validateHash("SHA1",  sha1.hexdigest(),             rom_data.get("sha1", ""))
        self._validateHash("CRC32", f"{crc32 & 0xffffffff:08x}", rom_data.get("crc32", ""))
      except ValueError:
        if os.path.exists(temp_path):
          os.remove(temp_path)
        raise

      os.replace(temp_path, output_path)
      return output_path

    except InterruptedError:
      raise  # keep .part for future resume
    except ValueError:
      raise  # .part already removed above
    except Exception:
      raise  # keep .part — network/IO error, resume later


  def _validateHash(self, label: str, actual: str, expected: str):
    if expected and actual.lower() != expected.lower():
      raise ValueError(f"{label} mismatch: expected {expected}, got {actual}")


  def _unzip(self, archive_path: str):
    import os, zipfile
    from py7zr import SevenZipFile

    extract_dir = os.path.realpath(os.path.dirname(archive_path))
    DebugHelper.print(DebugType.TYPE_INFO, f"Unzipping [{archive_path}]...", "unzip")
    if archive_path.lower().endswith('.zip'):
      with zipfile.ZipFile(archive_path) as archive:
        for member in archive.namelist():
          dest = os.path.realpath(os.path.join(extract_dir, member))
          if not dest.startswith(extract_dir + os.sep) and dest != extract_dir:
            raise ValueError(f"ZIP slip bloqueado: {member!r}")
        archive.extractall(extract_dir)
    else:
      with SevenZipFile(archive_path) as archive:
        archive.extractall(extract_dir)
    os.remove(archive_path)




class HashCheckWorker(QRunnable):
  """Compute MD5/SHA1/CRC32 of a file and emit results."""

  class _Sig(QObject):
    done  = pyqtSignal(dict)   # {"MD5": (actual, expected), ...}
    error = pyqtSignal(str)

  def __init__(self, file_path: str, expected: dict):
    super().__init__()
    self.setAutoDelete(True)
    self.signals   = self._Sig()
    self._path     = file_path
    self._expected = expected   # {"md5": "...", "sha1": "...", "crc32": "..."}

  def run(self):
    import hashlib, zlib
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    crc32 = 0
    try:
      with open(self._path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
          md5.update(chunk)
          sha1.update(chunk)
          crc32 = zlib.crc32(chunk, crc32)
      results = {
        "MD5":   (md5.hexdigest(),               self._expected.get("md5",   "")),
        "SHA1":  (sha1.hexdigest(),              self._expected.get("sha1",  "")),
        "CRC32": (f"{crc32 & 0xffffffff:08x}",  self._expected.get("crc32", "")),
      }
      self.signals.done.emit(results)
    except OSError as e:
      self.signals.error.emit(str(e))


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
