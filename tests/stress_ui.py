"""
Stress test — Responsividade da UI com catálogo de 40k ROMs (escala MAME).

Executa com: DISPLAY=:0 .venv/bin/python tests/stress_ui.py
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ─── QApplication antes de qualquer outro import de widget ───────────────────
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
app = QApplication(sys.argv)

import _constants
import _platforms
import _settings

# ─── Banco de dados em memória com 40k ROMs ───────────────────────────────────

_tmp = tempfile.mkdtemp(prefix="stress_ui_")
_db_path = os.path.join(_tmp, "stress.db")
os.makedirs(os.path.join(_tmp, "downloads"), exist_ok=True)

for mod, attr, val in [
    (_constants, "CACHE_DIR",               _tmp),
    (_constants, "PLATFORMS_CACHE_DB",      _db_path),
    (_constants, "PLATFORMS_CACHE_FILENAME", os.path.join(_tmp, "legacy.json")),
    (_constants, "SETTINGS_FILE",           os.path.join(_tmp, "settings.json")),
    (_constants, "CONFIG_DIR",              _tmp),
    (_constants, "DEFAULT_DOWNLOAD_DIR",    os.path.join(_tmp, "downloads")),
    (_platforms, "CACHE_DIR",               _tmp),
    (_platforms, "PLATFORMS_CACHE_DB",      _db_path),
    (_platforms, "PLATFORMS_CACHE_FILENAME", os.path.join(_tmp, "legacy.json")),
    (_settings,  "CACHE_DIR",               _tmp),
    (_settings,  "SETTINGS_FILE",           os.path.join(_tmp, "settings.json")),
    (_settings,  "CONFIG_DIR",              _tmp),
    (_settings,  "DEFAULT_DOWNLOAD_DIR",    os.path.join(_tmp, "downloads")),
]:
    setattr(mod, attr, val)

platforms_helper = _platforms.PlatformsHelper()
settings_helper  = _settings.SettingsHelper()
settings_helper.update(("download_path", os.path.join(_tmp, "downloads")))
settings_helper.update(("unzip", False))

# Seed: 5 plataformas, distribuição MAME-realista
PLATFORM_SIZES = {
    "Arcade - MAME":          40_000,
    "Nintendo - SNES":         3_572,
    "Nintendo - NES":          3_100,
    "Sega - Megadrive / Genesis": 1_200,
    "Atari 2600":                800,
}
print("\n" + "=" * 62)
print("  STRESS TEST — Responsividade UI com catálogo grande")
print("=" * 62)
print(f"  Populando banco de dados...")
t_seed = time.monotonic()
for platform, count in PLATFORM_SIZES.items():
    rows = [
        (platform, f"rom_{i:05d}", "stress-src", f"rom_{i:05d}.zip", 1_048_576, "", "", "", "zip")
        for i in range(count)
    ]
    platforms_helper._db.executemany(
        """
        INSERT OR IGNORE INTO roms
        (platform, name, source_id, file_path, size, md5, crc32, sha1, format)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
platforms_helper._db.commit()
platforms_helper._fts_available = platforms_helper._setup_fts()
total_roms = sum(PLATFORM_SIZES.values())
print(f"  {total_roms:,} ROMs em {len(PLATFORM_SIZES)} plataformas  ({time.monotonic() - t_seed:.2f}s)")
print()

# ─── Stub de updater mínimo ───────────────────────────────────────────────────

from unittest.mock import MagicMock
updater_mock = MagicMock()
updater_mock.currentVersionString.return_value = "2.1.0"
updater_mock.lastestVersionString.return_value = "2.1.0"
updater_mock.updateAvailable.return_value = False

# ─── Carrega MainWindow ───────────────────────────────────────────────────────

from mainwindow import MainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem

print("  Criando MainWindow...")
t0 = time.monotonic()
window = MainWindow(settings_helper, updater_mock, platforms_helper)
window.show()
app.processEvents()
t_mw = time.monotonic() - t0
print(f"  MainWindow criada e exibida:  {t_mw * 1000:.0f} ms")
print()

results = []

def bench(label: str, fn, reps: int = 1):
    times = []
    for _ in range(reps):
        t = time.monotonic()
        fn()
        app.processEvents()
        times.append((time.monotonic() - t) * 1000)
    avg = sum(times) / len(times)
    best = min(times)
    results.append((label, avg, best, reps))
    tag = "OK" if avg < 1000 else "LENTO"
    print(f"  [{tag}]  {label}")
    print(f"          avg={avg:.0f}ms  best={best:.0f}ms  (n={reps})")

# ─── Benchmark 1: selecionar plataforma MAME (40k ROMs) ──────────────────────

def _select_platform(name: str):
    """Seleciona plataforma na sidebar pelo nome."""
    for i in range(window.lw_platforms.count()):
        item = window.lw_platforms.item(i)
        if item and item.data(Qt.ItemDataRole.UserRole) == name:
            window.lw_platforms.setCurrentItem(item)
            window._onListwidgetSelectionChanged(item)
            app.processEvents()
            return

print("  Benchmarks de seleção de plataforma")
print("  " + "-" * 58)

# Primeiro acesso (cold): carrega chunk de 500 do MAME
bench("Selecionar MAME (40k ROMs) — 1ª vez [cold]",
      lambda: _select_platform("Arcade - MAME"))

# Segundo acesso (warm): dados já carregados em memória
bench("Selecionar MAME (40k ROMs) — 2ª vez [warm]",
      lambda: _select_platform("Arcade - MAME"))

bench("Selecionar SNES (3.5k ROMs)",
      lambda: _select_platform("Nintendo - SNES"))

bench("Selecionar NES (3.1k ROMs)",
      lambda: _select_platform("Nintendo - NES"))

# ─── Benchmark 2: filtro de busca (FTS5) na plataforma MAME ─────────────────

_select_platform("Arcade - MAME")
app.processEvents()

print()
print("  Benchmarks de filtro FTS5 (MAME — 40k ROMs)")
print("  " + "-" * 58)

def _set_filter(text: str):
    window.le_filter.setText(text)
    window.filter_timer.stop()   # cancel debounce; we drive the call explicitly below
    app.processEvents()
    window._applyTableFilter()
    app.processEvents()

bench('Filtro "pac"    (prefixo curto)',
      lambda: _set_filter("pac"), reps=5)

bench('Filtro "street fighter"  (dois tokens)',
      lambda: _set_filter("street fighter"), reps=5)

bench('Filtro "zzz_nomatch"  (zero resultados)',
      lambda: _set_filter("zzz_nomatch"), reps=5)

bench('Limpar filtro  (volta ao chunk 500)',
      lambda: _set_filter(""), reps=5)

# ─── Benchmark 3: navegação entre plataformas (leak de memória) ──────────────

import tracemalloc, gc

print()
print("  Benchmark de navegação — 10× rotação entre plataformas")
print("  " + "-" * 58)

PLATFORMS_CYCLE = list(PLATFORM_SIZES.keys())
tracemalloc.start()
snapshot_before = tracemalloc.take_snapshot()

t_nav = time.monotonic()
for cycle in range(2):
    for pname in PLATFORMS_CYCLE:
        _select_platform(pname)
        app.processEvents()
elapsed_nav = (time.monotonic() - t_nav) * 1000
print(f"  10 navegações:  {elapsed_nav:.0f} ms  ({elapsed_nav/10:.0f} ms/plataforma avg)")

gc.collect()
snapshot_after = tracemalloc.take_snapshot()
tracemalloc.stop()

top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
leaked = sum(s.size_diff for s in top_stats if s.size_diff > 0)
print(f"  Crescimento de memória Python: {leaked / 1024:.1f} KB")
print()

# ─── Benchmark 4: item count na tabela após clear ────────────────────────────

print("  Verificação de limpeza da tabela")
print("  " + "-" * 58)
_select_platform("Arcade - MAME")
app.processEvents()
rows_mame = window.tw_romsList.rowCount()

_select_platform("Atari 2600")
app.processEvents()
rows_atari = window.tw_romsList.rowCount()

_select_platform("Arcade - MAME")
app.processEvents()
rows_mame2 = window.tw_romsList.rowCount()

_chunk = window._CHUNK_SIZE
_atari_expected = min(PLATFORM_SIZES["Atari 2600"], _chunk)
print(f"  MAME carregado:         {rows_mame} linhas  (chunk {_chunk} esperado)")
print(f"  Atari 2600 carregado:   {rows_atari} linhas  ({_atari_expected} esperado de {PLATFORM_SIZES['Atari 2600']} ROMs)")
print(f"  MAME recarregado:       {rows_mame2} linhas")
rows_ok = (rows_mame == rows_mame2 and rows_atari == _atari_expected)
print(f"  Linhas corretas:        {'OK ✓' if rows_ok else 'FALHOU ✗'}")
print()

# ─── Relatório final ─────────────────────────────────────────────────────────

print("=" * 62)
print("  RESULTADOS COMPLETOS")
print("=" * 62)
print(f"  {'Operação':<42}  {'avg':>6}  {'best':>6}")
print(f"  {'-'*42}  {'------':>6}  {'------':>6}")
for label, avg, best, reps in results:
    flag = " ⚠" if avg > 500 else ""
    print(f"  {label:<42}  {avg:>5.0f}ms  {best:>5.0f}ms{flag}")

print()
all_ok = all(avg < 1000 for _, avg, _, _ in results) and rows_ok
print("  Veredicto:", "PASSOU ✓" if all_ok else "ATENÇÃO — algum benchmark excedeu 1s")
print("=" * 62 + "\n")

from PyQt6.QtCore import QThreadPool, QTimer
QThreadPool.globalInstance().waitForDone(2000)  # drain pending fetchers before Qt teardown
QTimer.singleShot(0, app.quit)
window.close()
app.exec()  # run event loop briefly so Qt can process close + thread cleanup
import os
sys.stdout.flush()
os._exit(0 if all_ok else 1)  # bypass Python teardown to avoid Qt destructor segfault
