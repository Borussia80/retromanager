"""
Stress test — DownloadEngine concurrency, retry e cancelamento.

Executa com: .venv/bin/python tests/stress_download.py
"""
import os
import sys
import tempfile
import threading
import time
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtCore import QCoreApplication, QTimer

app = QCoreApplication(sys.argv)

import _constants
import _platforms
import _settings

# ─── Banco de dados em memória (12 ROMs fictícias) ────────────────────────────

_tmp = tempfile.mkdtemp(prefix="stress_dl_")
_constants.CACHE_DIR = _tmp
_constants.PLATFORMS_CACHE_DB = os.path.join(_tmp, "stress.db")
_constants.PLATFORMS_CACHE_FILENAME = os.path.join(_tmp, "legacy.json")
_constants.SETTINGS_FILE = os.path.join(_tmp, "settings.json")
_constants.CONFIG_DIR = _tmp
_constants.DEFAULT_DOWNLOAD_DIR = os.path.join(_tmp, "downloads")
_platforms.CACHE_DIR = _tmp
_platforms.PLATFORMS_CACHE_DB = os.path.join(_tmp, "stress.db")
_platforms.PLATFORMS_CACHE_FILENAME = os.path.join(_tmp, "legacy.json")
_settings.CACHE_DIR = _tmp
_settings.SETTINGS_FILE = os.path.join(_tmp, "settings.json")
_settings.CONFIG_DIR = _tmp
_settings.DEFAULT_DOWNLOAD_DIR = os.path.join(_tmp, "downloads")
os.makedirs(os.path.join(_tmp, "downloads"), exist_ok=True)

platforms = _platforms.PlatformsHelper()
settings  = _settings.SettingsHelper()
settings.update(("download_path", os.path.join(_tmp, "downloads")))
settings.update(("unzip", False))
settings.update(("organize_by_platform", False))

ROMS = [(f"Stress Platform", f"rom_{i:02d}") for i in range(12)]
platforms._db.executemany(
    "INSERT OR IGNORE INTO roms VALUES (?,?,?,?,?,?,?,?,?)",
    [(p, r, "stress-src", f"{r}.zip", 102400, "", "", "", "zip") for p, r in ROMS],
)
platforms._db.commit()

# ─── Métricas coletadas durante o teste ───────────────────────────────────────

_lock = threading.Lock()
_peak_threads = 0
_completed: list[str] = []
_failed: list[str] = []
_retried: set[str] = set()
_fail_once: set[str] = {r for _, r in ROMS[:3]}   # primeiros 3 falham na 1ª tentativa

_original_download_call_count: dict[str, int] = {}


def _fake_download(self, platform: str, rom_name: str) -> str:
    """Simula download: 80–150 ms de latência, escreve 100 KB no disco."""
    global _peak_threads

    call_n = _original_download_call_count.get(rom_name, 0) + 1
    _original_download_call_count[rom_name] = call_n

    if rom_name in _fail_once and call_n == 1:
        with _lock:
            _retried.add(rom_name)
        # ValueError é capturado pelo DownloadWorker.run() e vira failedItem
        raise ValueError(f"[mock] falha intencional na 1ª tentativa de {rom_name}")

    # Mede pico de paralelismo
    active = threading.active_count()
    with _lock:
        if active > _peak_threads:
            _peak_threads = active

    # Simula latência de rede proporcional ao índice
    idx = int(rom_name.split("_")[1])
    time.sleep(0.08 + (idx % 3) * 0.04)

    # Escreve arquivo fictício
    dl_dir = settings.get("download_path")
    out = os.path.join(dl_dir, f"{rom_name}.zip")
    with open(out, "wb") as f:
        f.write(b"\x00" * 102400)
    return out


# ─── Testa retry com delays zero para não esperar 5s+ ─────────────────────────

from download_engine import DownloadEngine
DownloadEngine.RETRY_DELAYS = [0, 0, 0]

# ─── Wiring ───────────────────────────────────────────────────────────────────

engine = DownloadEngine(settings, platforms, ROMS, max_concurrent=3)
_engine_thread = None

results = {
    "completed": 0,
    "failed": 0,
    "retried": 0,
    "cancelled": False,
    "wall_time": 0.0,
    "peak_threads": 0,
}

def on_completed(platform, rom_name):
    _completed.append(rom_name)
    results["completed"] += 1

def on_failed(platform, rom_name, error):
    _failed.append(rom_name)
    results["failed"] += 1

def on_finished():
    results["wall_time"] = time.monotonic() - _t0
    results["peak_threads"] = _peak_threads
    results["retried"] = len(_retried)
    app.quit()

engine.completedItem.connect(on_completed)
engine.failedItem.connect(on_failed)
engine.finished.connect(on_finished)

# ─── Run ──────────────────────────────────────────────────────────────────────

print("\n" + "=" * 58)
print("  STRESS TEST — DownloadEngine concorrência + retry")
print("=" * 58)
print(f"  ROMs na fila:     {len(ROMS)}")
print(f"  MAX_CONCURRENT:   3")
print(f"  Falhas simuladas: 3 (rom_00, rom_01, rom_02 → 1 retry cada)")
print()

# Tempo mínimo esperado se tudo fosse sequencial (sum das latências)
sequential_min = sum(0.08 + (i % 3) * 0.04 for i in range(12))
print(f"  Tempo mínimo sequencial estimado: {sequential_min:.2f}s")
print(f"  Tempo ótimo paralelo estimado:    ~{sequential_min / 3:.2f}s  (3 workers)")
print()

_t0 = time.monotonic()

with patch("_tools.DownloadWorker._download", _fake_download):
    # Inicia o engine na thread principal via QTimer (drop-in com mainwindow.py)
    _engine_thread = __import__("PyQt6.QtCore", fromlist=["QThread"]).QThread()
    engine.moveToThread(_engine_thread)
    _engine_thread.started.connect(engine.run)
    engine.finished.connect(_engine_thread.quit)
    _engine_thread.start()

    # Timeout de segurança: 30s
    _guard = QTimer()
    _guard.setSingleShot(True)
    _guard.timeout.connect(lambda: (print("TIMEOUT"), app.quit()))
    _guard.start(30_000)

    app.exec()

# ─── Relatório ────────────────────────────────────────────────────────────────

print("=" * 58)
print("  RESULTADOS")
print("=" * 58)
wall = results["wall_time"]
print(f"  Tempo real (wall):     {wall:.3f}s")
print(f"  Speedup vs sequencial: {sequential_min / wall:.2f}×  (ideal ~3×)")
print(f"  Concorrência de pico:  {results['peak_threads']} threads ativas simultâneas")
print()
print(f"  Completados:  {results['completed']} / {len(ROMS)}")
print(f"  Falhos:       {results['failed']}")
print(f"  Retentativas: {results['retried']}  (esperado: 3)")
print()

# Verifica vazamento de threads
remaining = threading.active_count()
print(f"  Threads ativas após fim: {remaining}  (esperado: 1 — thread principal)")

# Verifica arquivos no disco
dl_dir = settings.get("download_path")
files = [f for f in os.listdir(dl_dir) if f.endswith(".zip")]
print(f"  Arquivos gravados:       {len(files)} / {len(ROMS)}  (.zip)")
print()

# Veredicto
ok = (
    results["completed"] == len(ROMS)
    and results["failed"] == 0
    and results["retried"] == 3
    and wall < sequential_min  # paralelo deve ser mais rápido
)
print("  Veredicto:", "PASSOU ✓" if ok else "FALHOU ✗")
print("=" * 58 + "\n")
sys.exit(0 if ok else 1)
