# RetroManager v2.2 — Roadmap de Correções, Arquitetura e Evolução para 10/10

> **Documento de referência para desenvolvimento.** Use este arquivo como prompt
> de contexto completo ao iniciar cada sessão de trabalho na v2.2.
> Cada seção é autocontida e pode ser executada independentemente.

---

## 0. Estado atual da base de código

| Dimensão            | Nota atual | Meta v2.2 |
|---------------------|:----------:|:---------:|
| Arquitetura         | 7.5        | 9         |
| Organização         | 7.0        | 9         |
| Concorrência        | 6.0        | 9         |
| Performance         | 6.0        | 8         |
| Segurança           | 6.0        | 9         |
| Robustez            | 6.0        | 9         |
| Escalabilidade      | 6.0        | 8         |
| UX                  | 6.0        | 9         |
| Observabilidade     | 3.0        | 8         |
| Readiness produção  | 6.0        | 9         |

**Stack:** Python 3.12+, PyQt6, SQLite 3, requests, py7zr  
**Plataforma alvo:** Linux (Fedora/Ubuntu/Arch), empacotamento AppImage + Flatpak

### Metas de performance obrigatórias — baseline antes do Sprint PERF

| Métrica                        | Valor atual (estimado) | Meta v2.2 |
|-------------------------------|:----------------------:|:---------:|
| Startup cold (sem cache)      | ~4–6s                  | < 2s      |
| Startup warm (com cache)      | ~2–3s                  | < 800ms   |
| Busca (keystroke → resultado) | ~200–500ms             | < 50ms    |
| Scroll FPS (MAME 40k ROMs)    | ~20–30 FPS             | 60 FPS    |
| Thumbnail load (disk hit)     | ~80–150ms              | < 30ms    |
| Thumbnail load (network)      | ~1–3s                  | < 100ms   |
| Download retry delay          | manual                 | < 5s auto |
| Footprint de memória (idle)   | ~90–130 MB             | < 80 MB   |
| Footprint (MAME carregado)    | ~200–300 MB            | < 150 MB  |

> Medir **antes** de qualquer otimização do Sprint 2. Sem baseline, otimização é chute.

---

## 1. SPRINT 0 — Correções críticas obrigatórias antes de qualquer feature

> Estas correções devem ser aplicadas antes de qualquer outra mudança.
> Todas são quebras de comportamento confirmadas em runtime.

---

### BUG-001 · `NameError` silencioso no downloader  
**Arquivo:** `_tools.py`  
**Impacto:** Todos os erros de rede no `DownloadWorker` são silenciados; `failedItem` nunca dispara; a UI trava aguardando sinal que não chega.

**Causa:** `requests` é importado localmente dentro de `_download()`, mas o `except` de `run()` referencia `requests.exceptions.RequestException` sem importação no escopo da função.

```python
# ANTES — _tools.py linha 178
except (requests.exceptions.RequestException, ValueError, zipfile.BadZipFile) as e:

# DEPOIS — adicionar no topo do módulo, junto aos outros imports
import requests       # ← uma linha resolve o bug inteiro
import zipfile
import threading
```

---

### BUG-002 · `selectionChanged` nunca dispara no `DownloadQueue`  
**Arquivo:** `download_queue.py`  
**Impacto:** O botão "Excluir" fica permanentemente desabilitado; itens selecionados na fila não podem ser removidos individualmente.

**Causa:** Atribuição de atributo Python não sobrescreve virtual C++ do Qt.

```python
# ANTES
self.lwToDownload.selectionChanged = self._onSelectionChanged

# DEPOIS
self.lwToDownload.selectionModel().selectionChanged.connect(
    self._onSelectionChanged
)
```

---

### BUG-003 · Comparação de nome de ROM usa display text em vez de shortname  
**Arquivos:** `mainwindow.py` — `_onDownloadCompletedItem` e `_toggleFavorite`  
**Impacto:** Badge ✓ de download baixado e toggle de favorito não funcionam para nenhuma ROM do MAME; o `it.text()` retorna nome amigável ("Pac-Man") mas `rom_name` é o shortname interno ("pacman").

```python
# ANTES — em ambos os métodos
if it and it.text() == rom_name:

# DEPOIS — usar shortname armazenado em UserRole+3
shortname = it.data(Qt.ItemDataRole.UserRole + 3) or it.text()
if it and shortname == rom_name:
```

---

### BUG-004 · Badge ✓ de download aparece à esquerda das tags de região  
**Arquivo:** `platform_icons.py` — `GameTitleDelegate.paint`  
**Impacto:** O checkmark de ROM baixada se posiciona à esquerda de todas as badges de região, não à direita como esperado.

**Causa:** O checkmark é medido *após* o loop que consome `x_right` da direita para a esquerda.

```python
# DEPOIS — medir o checkmark ANTES do loop de tags
if downloaded:
    chk_text = "✓"
    chk_w = bfm.horizontalAdvance(chk_text) + self._BADGE_PAD_H * 2
    chk_h = bfm.height() + self._BADGE_PAD_V * 2
    chk_y = rect.top() + (rect.height() - chk_h) // 2
    chk_r = QRect(x_right - chk_w, chk_y, chk_w, chk_h)
    # … desenhar …
    x_right -= chk_w + 4

for tag in reversed(tags):   # ← só depois processar as region tags
    …
```

---

### BUG-005 · `_current_platform()` chamado duas vezes — possível race condition  
**Arquivo:** `mainwindow.py` — `_openInRetroArch`, `_addToRetroArchPlaylist`, `_addToLutris`, `_checkRomIntegrity`  
**Impacto:** Se o usuário clicar em outra plataforma entre as duas chamadas, `platform` e o argumento de `find_rom_file` podem divergir.

```python
# ANTES
platform = self._current_platform()
rom_path = library_service.find_rom_file(
    self.settings, rom_name, self._current_platform()   # ← segunda leitura
)

# DEPOIS
platform = self._current_platform()
rom_path = library_service.find_rom_file(self.settings, rom_name, platform)
```

---

### BUG-006 · `EOFError` silenciado em `SettingsHelper._read()`  
**Arquivo:** `_settings.py`  
**Impacto:** Arquivo de configuração vazio ou corrompido é ignorado silenciosamente; o usuário perde caminho de download e todas as preferências sem aviso algum.

```python
# ANTES
except EOFError: pass

# DEPOIS
except EOFError:
    DebugHelper.print(DebugType.TYPE_ERROR,
                      "settings.json vazio ou corrompido — usando padrões.", "SETTINGS")
    self._fix({})
```

---

### BUG-007 · Verificação de settings por contagem de chaves, não por conteúdo  
**Arquivo:** `_settings.py` — `_read()`  
**Impacto:** Se uma chave for renomeada entre versões, a contagem pode bater mas as chaves serem diferentes; `_fix()` é ignorado e o app crasha em `get()` com `ValueError`.

```python
# ANTES
if len(temp_settings.keys()) != len(self._settings.keys()):

# DEPOIS
if set(temp_settings.keys()) != set(self._settings.keys()):
```

---

### BUG-008 · Updates de patch (REVISION) nunca detectados  
**Arquivo:** `_updater.py` — `updateAvailable()`  
**Impacto:** v2.1.0 instalado, v2.1.5 disponível → retorna `False`; o usuário nunca é avisado de bugfixes de patch.

```python
# DEPOIS — adicionar terceira condição
def updateAvailable(self) -> bool:
    self._fetchLatestRelease()
    cur = (VERSION_MAJOR, VERSION_MINOR, VERSION_REVISION)
    lat = (self.LASTEST_MAJOR, self.LASTEST_MINOR, self.LASTEST_REVISION)
    if lat > cur:
        DebugHelper.print(DebugType.TYPE_INFO, "Update available!", "UPDATER")
        return True
    DebugHelper.print(DebugType.TYPE_INFO, "You have the latest version.", "UPDATER")
    return False
```

---

### BUG-009 · SQLite sem lock em acesso multithread  
**Arquivos:** `_platforms.py`, `history_manager.py`  
**Impacto:** `PlatformsHelper` é chamado da main thread e do `DownloadWorker` simultaneamente; sem serialização pode corromper cursores.

```python
# DEPOIS — adicionar em ambas as classes
import threading

class PlatformsHelper:
    def __init__(self):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(PLATFORMS_CACHE_DB, check_same_thread=False)
        …

    def getRom(self, platform_name: str, rom_name: str) -> RomEntry | None:
        with self._lock:
            row = self._db.execute(…).fetchone()
        …
```

---

### BUG-010 · Classe `_Worker` morta em `_loadMameNamesAsync`  
**Arquivo:** `mainwindow.py`  
**Impacto:** Código morto — a classe `_Worker(QRunnable)` é definida mas nunca instanciada. Confunde leitores e engana IDEs.

**Ação:** Remover completamente o bloco `_Worker` (linhas antes de `_Loader`).

---

## 2. Refatorações de qualidade — SPRINT 1

> Não mudam comportamento externo, mas eliminam dívida técnica estrutural.

---

### REF-001 · `@staticmethod` ausente em `Tools` e `DebugHelper`

```python
# _tools.py
class Tools:
    @staticmethod
    def convertSizeToReadable(size: int) -> str: …

    @staticmethod
    def isCacheValid(validity_days: int) -> bool: …

# _debug.py
class DebugHelper:
    @staticmethod
    def print(debug_type, debug_message, debug_module=None): …
```

---

### REF-002 · `SettingsHelper.get()` e `update()` — trocar loop por acesso direto

```python
def get(self, option: str):
    try:
        return self._settings[option]
    except KeyError:
        raise ValueError(f"Setting <{option}> not found.")

def update(self, option: tuple[str, Any]):
    key, value = option
    if key not in self._settings:
        raise ValueError(f"Setting <{key}> not found.")
    self._settings[key] = value
    DebugHelper.print(DebugType.TYPE_DEBUG, f"'{key}' → {value!r}", "SETTINGS")
```

---

### REF-003 · Import de `_tools.Tools` no topo de `rom_detail_panel.py`

```python
# ANTES — import local dentro de show_rom()
def show_rom(self, …):
    from _tools import Tools   # ← chamado a cada seleção de ROM

# DEPOIS — mover para o topo do arquivo
from _tools import Tools
```

---

### REF-004 · Injeção YAML em `lutris_helper.py`

```python
# ANTES — f-string sem escape
yaml_text = f"name: {clean}\n    working_dir: {work_dir}\n"

# DEPOIS — usar PyYAML
import yaml
script_block = {
    "name": clean,
    "game_slug": slug,
    "version": "RetroArch",
    "runner": "linux",
    "script": {
        "game": {
            "exe": exe,
            "args": args_str,
            "working_dir": work_dir,
        }
    }
}
yaml_text = yaml.dump(script_block, allow_unicode=True)
```

---

### REF-005 · Wildcard imports em `mainwindow.py` e `download_queue.py`

Substituir `from PyQt6.QtCore import *` por imports explícitos, seguindo o padrão já adotado nos demais módulos (`rom_detail_panel.py`, `platform_icons.py`, etc.).

---

### REF-006 · Inconsistência de filtro fuzzy entre lista e grid

`library_service.rom_matches_filters()` implementa subsequência fuzzy (3+ chars); `_RomFilterProxy` na grid usa substring simples. Unificar:

```python
# game_grid.py — _RomFilterProxy.filterAcceptsRow
from library_service import rom_matches_filters

def filterAcceptsRow(self, source_row, source_parent):
    idx = self.sourceModel().index(source_row, 0, source_parent)
    name = idx.data(Qt.ItemDataRole.DisplayRole) or ""
    return rom_matches_filters(name, self._keywords, self._region)
```

---

### REF-007 · `retroarch_helper._empty_playlist` — parâmetro `db_name` ignorado

O parâmetro existe mas o dict retornado não o usa. Ou remover o parâmetro, ou verificar se o formato LPL precisa de algum campo com esse valor e adicioná-lo.

---

### REF-008 · `_platforms.py` — `getPlatformName` e `getRomName` ineficientes

```python
# ANTES — carrega todas as linhas para pegar uma por índice
def getPlatformName(self, index: int) -> str:
    rows = self._db.execute("SELECT DISTINCT platform …").fetchall()
    return rows[index][0]

# DEPOIS — usar LIMIT/OFFSET
def getPlatformName(self, index: int) -> str:
    with self._lock:
        row = self._db.execute(
            "SELECT DISTINCT platform FROM roms ORDER BY platform LIMIT 1 OFFSET ?",
            (index,)
        ).fetchone()
    return row[0] if row else ""
```

---

## 2.5. SPRINT PERF — Profiling obrigatório antes das features de performance

> Executar **após** Sprint 1 e **antes** do Sprint 2.  
> Nenhuma otimização deve ser escrita sem dados reais de profiling.  
> Otimização sem medição é refatoração aleatória.

---

### PERF-001 · Instrumentação de startup

```python
# _bootstrap.py — adicionar timing de inicialização
import time

class StartupTimer:
    """Mede e loga o tempo de cada fase do startup."""
    _marks: dict[str, float] = {}

    @classmethod
    def mark(cls, label: str):
        cls._marks[label] = time.perf_counter()
        log.debug("startup · %-28s → %6.0f ms", label,
                  (cls._marks[label] - cls._marks.get("_start", cls._marks[label])) * 1000)

    @classmethod
    def report(cls):
        start = cls._marks.get("_start", 0)
        log.info("=== Startup report ===")
        for label, t in cls._marks.items():
            log.info("  %-30s %6.0f ms", label, (t - start) * 1000)

# Uso em app.pyw
StartupTimer.mark("_start")
StartupTimer.mark("imports_done")
StartupTimer.mark("qapp_created")
StartupTimer.mark("mainwindow_created")
StartupTimer.mark("platforms_loaded")
StartupTimer.report()
```

---

### PERF-002 · CPU profiling com py-spy e cProfile

```bash
# Instalar
pip install py-spy scalene

# Flame graph de uma sessão completa (abre no browser)
py-spy record -o profile.svg -- python app.pyw

# Profile de função específica
python -m cProfile -o profile.out app.pyw
python -m pstats profile.out
# No prompt pstats: sort cumulative / stats 20

# scalene — CPU *e* memória linha a linha
scalene app.pyw
```

**Pontos obrigatórios a medir:**
- `_onListwidgetSelectionChanged` — carregamento de ROMs na sidebar
- `_applyTableFilter` — cada keystroke no campo de busca
- `GameTitleDelegate.paint` — repaint de cada célula da tabela
- `scan_downloaded` — scan do filesystem por ROMs baixadas
- `_mame_names.load` — parse/load do cache MAME

---

### PERF-003 · Memory profiling com tracemalloc e objgraph

```python
# Adicionar em _bootstrap.py (apenas quando DEBUG >= 3)
import tracemalloc
import objgraph   # pip install objgraph

def start_memory_profiling():
    tracemalloc.start(25)   # 25 frames de stack

def snapshot_memory(label: str = ""):
    snapshot = tracemalloc.take_snapshot()
    top = snapshot.statistics("lineno")[:15]
    log.debug("=== Memory snapshot: %s ===", label)
    for stat in top:
        log.debug("  %s", stat)

def check_leaks():
    """Chamar após fechar uma plataforma e abrir outra — deve ser estável."""
    objgraph.show_most_common_types(limit=10)
    objgraph.show_growth(limit=10)  # objetos que crescem = candidatos a leak
```

**Cenários obrigatórios a medir:**
- Abrir MAME (40k ROMs) → fechar → abrir SNES → memória deve recuar
- Navegar entre 10 plataformas sem crescimento linear de `QPixmap`
- Download de 5 ROMs seguidos sem crescimento de `QThread` objects
- `QTableWidgetItem` count deve ser zero após `setRowCount(0)`

---

### PERF-004 · Render timing no delegate

```python
# GameTitleDelegate.paint — instrumentação temporária, remover após profiling
import time

def paint(self, painter, option, index):
    t0 = time.perf_counter()
    # … código existente …
    elapsed_us = (time.perf_counter() - t0) * 1_000_000
    if elapsed_us > 500:   # > 500 µs por célula = problema de repaint
        log.debug("paint slow: row=%d %.0fµs", index.row(), elapsed_us)
```

---

## 3. Arquitetura alvo — v2.2

> Objetivo: separar responsabilidades de forma que cada camada seja testável
> independentemente e o `MainWindow` deixe de ser um god object.

```
retromanager/
├── core/                        ← domínio puro, sem Qt
│   ├── models.py                (RomEntry, Platform, DownloadJob — dataclasses)
│   ├── settings.py              (SettingsHelper — refatorado com dataclass)
│   ├── library.py               (library_service — já bem encaminhado)
│   ├── catalog.py               (PlatformsHelper — já SQLite, adicionar lock)
│   ├── favorites.py             (FavoritesManager — já bom)
│   ├── history.py               (HistoryManager — adicionar lock)
│   └── events.py                (EventBus — NOVO, ver §3.1)
│
├── integrations/                ← wrappers para ferramentas externas
│   ├── retroarch.py             (RetroArchHelper)
│   ├── lutris.py                (LutrisHelper — corrigir YAML)
│   └── archive_org.py           (download + cache generator — NOVO, extraído de _tools.py)
│
├── workers/                     ← QObject/QRunnable workers, sem lógica de negócio
│   ├── download_worker.py       (DownloadWorker — extraído de _tools.py)
│   ├── hash_worker.py           (HashCheckWorker — extraído de _tools.py)
│   ├── thumbnail_worker.py      (ThumbnailFetcher — já separado, manter)
│   └── updater_worker.py        (UpdaterHelper — já separado, manter)
│
├── ui/
│   ├── mainwindow.py            (orquestração apenas — sem lógica de negócio)
│   ├── panels/
│   │   ├── sidebar.py           (lista de plataformas — NOVO, extraído de mainwindow)
│   │   ├── rom_list.py          (tabela + filtros — NOVO)
│   │   ├── rom_detail_panel.py  (já separado — manter)
│   │   └── download_panel.py    (já separado — manter)
│   ├── delegates/
│   │   ├── game_title_delegate.py   (extraído de platform_icons.py)
│   │   └── format_badge_delegate.py
│   ├── dialogs/
│   │   ├── options.py
│   │   ├── error_dialog.py
│   │   └── about.py
│   └── widgets/
│       ├── platform_icons.py    (widgets de sidebar — manter)
│       ├── game_grid.py         (manter)
│       └── empty_state.py       (manter)
│
├── cache/
│   ├── mame_names.py            (já separado — manter)
│   └── thumbnail_evict.py       (já separado — manter)
│
└── _bootstrap.py                (logging, QApplication, splash — NOVO)
```

---

### 3.1 EventBus — desacoplar MainWindow dos subsistemas

Problema atual: `MainWindow` conecta sinais diretamente entre `DownloadWorker`, `FavoritesManager`, `HistoryManager`, `RetroArchHelper` — criando dependências cruzadas.

**Implementação:**

```python
# core/events.py
from __future__ import annotations
from PyQt6.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    """Singleton de eventos de aplicação."""

    # Downloads
    download_started   = pyqtSignal(str, str)        # platform, rom_name
    download_completed = pyqtSignal(str, str)         # platform, rom_name
    download_failed    = pyqtSignal(str, str, str)    # platform, rom_name, error
    download_progress  = pyqtSignal(str, int, int, float)  # rom_name, done, total, speed

    # Biblioteca
    favorite_changed   = pyqtSignal(str, str, bool)  # platform, rom_name, is_fav
    history_updated    = pyqtSignal()

    # UI
    platform_selected  = pyqtSignal(str)             # platform_name | _FAVORITES_ | _HISTORY_
    filter_changed     = pyqtSignal(list, object)    # keywords, region

    _instance: EventBus | None = None

    @classmethod
    def get(cls) -> EventBus:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

**Uso em MainWindow (após refatoração):**

```python
bus = EventBus.get()
bus.download_completed.connect(self._on_download_completed)
bus.favorite_changed.connect(self._refresh_favorite_indicator)
# — sem referência direta a DownloadWorker ou FavoritesManager na UI layer
```

---

### 3.2 `SettingsHelper` como dataclass validada

```python
# core/settings.py
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

@dataclass
class AppSettings:
    cache_expiration: int    = 30
    check_updates: bool      = False
    download_path: str       = str(Path.home() / "ROMs")
    import_paths: list[str]  = field(default_factory=list)
    organize_by_platform: bool = True
    unzip: bool              = True

    def validate(self) -> list[str]:
        """Retorna lista de erros de validação."""
        errors = []
        if self.cache_expiration < -1:
            errors.append("cache_expiration deve ser >= -1")
        if self.download_path and not Path(self.download_path).parent.exists():
            errors.append(f"download_path inválido: {self.download_path}")
        return errors


class SettingsHelper:
    def __init__(self):
        self._path = Path(SETTINGS_FILE)
        self._data = AppSettings()
        self._load()

    def get(self, key: str):
        return getattr(self._data, key)   # AttributeError se chave inválida

    def update(self, option: tuple[str, Any]):
        key, value = option
        if not hasattr(self._data, key):
            raise AttributeError(f"Setting desconhecido: {key!r}")
        setattr(self._data, key, value)

    def write(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(asdict(self._data), indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    def _load(self):
        if not self._path.exists():
            self.write()
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            # Merge: preserva defaults para chaves novas, ignora chaves obsoletas
            known = {f.name for f in fields(AppSettings)}
            filtered = {k: v for k, v in raw.items() if k in known}
            self._data = AppSettings(**filtered)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            log.error("settings corrompido (%s) — usando padrões", e)
            self.write()
```

---

## 4. Melhorias de produto — SPRINT 2

> Features que elevam a qualidade percebida para nível de app desktop profissional.

---

### FEAT-001 · Download engine v2 — concorrência e retry automático

**Problema atual:** Downloads são sequenciais. Um arquivo lento bloqueia toda a fila.

```python
# workers/download_engine.py
class DownloadEngine(QObject):
    """Gerencia N downloads paralelos com retry exponencial."""

    MAX_CONCURRENT = 3         # configurável em Settings
    MAX_RETRIES    = 3
    RETRY_DELAYS   = [5, 30, 120]  # segundos

    def __init__(self, settings, platforms, max_concurrent=MAX_CONCURRENT):
        super().__init__()
        self._semaphore = QSemaphore(max_concurrent)
        self._workers: dict[str, DownloadWorker] = {}
        self._retry_counts: dict[str, int] = {}

    def enqueue(self, platform: str, rom_name: str): …
    def pause_all(self): …
    def resume_all(self): …
    def cancel(self, rom_name: str): …
```

---

### FEAT-002 · Busca com SQLite FTS5

**Problema atual:** Filtro via loop Python sobre `QTableWidget` — O(n) a cada keystroke com milhares de ROMs.

```sql
-- Migração de schema
CREATE VIRTUAL TABLE IF NOT EXISTS roms_fts USING fts5(
    name, platform,
    content='roms', content_rowid='rowid'
);

CREATE TRIGGER roms_ai AFTER INSERT ON roms BEGIN
    INSERT INTO roms_fts(rowid, name, platform) VALUES (new.rowid, new.name, new.platform);
END;
```

```python
# library_service.py
def search_roms(db, platform: str, query: str, limit=500) -> list[str]:
    if not query.strip():
        return [r[0] for r in db.execute(
            "SELECT name FROM roms WHERE platform=? ORDER BY name LIMIT ?",
            (platform, limit)
        )]
    # FTS5 com prefix match
    fts_query = " OR ".join(f'"{token}"*' for token in query.split())
    return [r[0] for r in db.execute(
        "SELECT roms.name FROM roms_fts JOIN roms ON roms.rowid = roms_fts.rowid "
        "WHERE roms_fts MATCH ? AND roms.platform=? ORDER BY rank LIMIT ?",
        (fts_query, platform, limit)
    )]
```

---

### FEAT-003 · Virtualização completa da lista de ROMs

**Problema atual:** `QTableWidget` carrega até 500 items DOM no chunk inicial; scroll em catálogos grandes (MAME: ~40k ROMs) ainda causa jank.

**Solução:** Migrar para `QAbstractTableModel` + `QTableView` (sem `QTableWidget`):

```python
# ui/panels/rom_list.py
class RomTableModel(QAbstractTableModel):
    """Modelo virtual — não cria items Qt; dados ficam no SQLite."""

    _COLS = ["Jogo", "Tamanho", "Formato", "MD5", "CRC32", "SHA1"]

    def __init__(self):
        super().__init__()
        self._rows: list[tuple] = []   # carregado sob demanda

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._rows[index.row()][index.column()]
        # UserRole, UserRole+1, etc. para flags de favorito/baixado
        …
```

---

### FEAT-004 · Providers de metadados (ScreenScraper / IGDB)

```python
# integrations/metadata.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class RomMetadata:
    title: str          = ""
    description: str    = ""
    genre: str          = ""
    year: int           = 0
    rating: float       = 0.0
    cover_url: str      = ""
    screenshot_url: str = ""
    developer: str      = ""
    publisher: str      = ""


class MetadataProvider(ABC):
    @abstractmethod
    async def fetch(self, platform: str, rom_name: str) -> RomMetadata | None: …


class ScreenScraperProvider(MetadataProvider):
    """https://www.screenscraper.fr/api2/ — requer conta gratuita."""
    …

class IGDBProvider(MetadataProvider):
    """https://api.igdb.com/v4 — requer client_id Twitch."""
    …

class MetadataCache:
    """SQLite local para evitar requests repetidos."""
    …
```

---

### FEAT-005 · Smart Collections (coleções automáticas)

```python
# core/collections.py
from dataclasses import dataclass
from typing import Callable

@dataclass
class Collection:
    name: str
    icon: str
    predicate: Callable[[str, str], bool]   # (platform, rom_name) -> bool


BUILT_IN_COLLECTIONS = [
    Collection("Baixados",   "⬇",  lambda p, r: library_service.find_rom_file(...)),
    Collection("Não jogados","◌",  lambda p, r: not history.was_played(p, r)),
    Collection("Completados","✓",  lambda p, r: progress.is_complete(p, r)),
    Collection("Clássicos",  "★",  lambda p, r: metadata.rating(p, r) >= 8.0),
    Collection("Anos 90",    "📼", lambda p, r: metadata.year(p, r) in range(1990, 2000)),
]
```

---

### FEAT-006 · Progresso de jogo e save states

```python
# core/progress.py — integração com RetroArch save states
class ProgressManager:
    def sync_from_retroarch(self, retroarch_dir: Path): …
    def mark_complete(self, platform: str, rom_name: str): …
    def playtime(self, platform: str, rom_name: str) -> int: …   # segundos
```

---

### FEAT-007 · Notificações nativas do sistema

```python
# ui/notifications.py
from PyQt6.QtCore import QObject
import subprocess, shutil

class Notifier(QObject):
    def send(self, title: str, body: str, icon: str = ""):
        if shutil.which("notify-send"):
            cmd = ["notify-send", "-a", "RetroManager"]
            if icon:
                cmd += ["-i", icon]
            subprocess.Popen(cmd + [title, body])
        # Fallback: QSystemTrayIcon.showMessage()
```

Uso após download completo:
```python
Notifier().send("Download concluído", f"{rom_name} está pronto para jogar.")
```

---

### FEAT-008 · Tema claro / sistema

```python
# theme.py — adicionar
LIGHT_THEME = """
QWidget { background-color: #f5f7fa; color: #1a2035; … }
…
"""

# _settings.py — adicionar campo
theme: str = "dark"   # "dark" | "light" | "system"
```

```python
# _bootstrap.py
from PyQt6.QtGui import QPalette
def apply_theme(app: QApplication, theme: str):
    if theme == "system":
        palette = app.palette()
        is_dark = palette.color(QPalette.ColorRole.Window).lightness() < 128
        theme = "dark" if is_dark else "light"
    app.setStyleSheet(DARK_THEME if theme == "dark" else LIGHT_THEME)
```

---

### FEAT-009 · Sistema de plugins

**Por que faz sentido para o RetroManager:** o domínio de retrogaming tem proliferação natural de pontos de extensão — dezenas de emuladores, múltiplos providers de metadados, fontes de ROMs alternativas, formatos de exportação (Pegasus Frontend, EmulationStation, LaunchBox). Sem plugin system, cada nova integração vira PR no core. Com ele, a comunidade resolve sozinha.

**Estratégia em três fases — sem overengineering:**

---

#### Fase 1 (v2.2) — Interfaces abstratas: extrair o que já existe

RetroArch e Lutris **já são plugins** — só falta a interface formal:

```python
# core/plugins/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    author: str
    plugin_type: str                        # "emulator" | "metadata" | "source" | "exporter"
    capabilities: list[str] = field(default_factory=list)  # ["network", "filesystem", "subprocess"]
    description: str = ""


class EmulatorPlugin(ABC):
    """RetroArch e Lutris viram implementações desta interface."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def detected(self) -> bool: ...

    @abstractmethod
    def launch(self, platform: str, rom_path: str) -> bool: ...

    @abstractmethod
    def add_to_library(self, platform: str, rom_name: str, rom_path: str) -> bool: ...

    def library_count(self) -> int:
        return 0   # opcional — implementar se suportado


class MetadataPlugin(ABC):
    """ScreenScraper, IGDB — implementações de FEAT-004."""

    @abstractmethod
    def fetch(self, platform: str, rom_name: str) -> "RomMetadata | None": ...

    @abstractmethod
    def supported_platforms(self) -> list[str]: ...

    def rate_limit_remaining(self) -> int:
        return -1   # -1 = desconhecido


class RomSourcePlugin(ABC):
    """Archive.org é a implementação nativa."""

    @abstractmethod
    def search(self, platform: str, query: str) -> list["RomEntry"]: ...

    @abstractmethod
    def download_url(self, entry: "RomEntry") -> str: ...


class ExporterPlugin(ABC):
    """Exporta biblioteca para outros frontends (Pegasus, EmulationStation, etc.)."""

    @abstractmethod
    def export(self, roms: list[tuple[str, str]], output_dir: str) -> bool: ...

    @abstractmethod
    def format_name(self) -> str: ...
```

---

#### Fase 2 (v2.3) — Descoberta e carregamento de plugins externos

```
~/.config/retromanager/plugins/
├── dolphin/
│   ├── plugin.toml      ← manifest declarativo
│   └── __init__.py      ← implementa EmulatorPlugin
├── screenscraper/
│   ├── plugin.toml
│   └── __init__.py
└── pegasus-exporter/
    ├── plugin.toml
    └── __init__.py
```

```toml
# plugin.toml — exemplo para integração com Dolphin
[plugin]
id          = "dolphin-integration"
name        = "Dolphin Emulator"
version     = "1.0.0"
author      = "community"
plugin_type = "emulator"

[capabilities]
required = ["subprocess"]      # usuário vê isto antes de ativar
optional = ["filesystem"]
```

```python
# core/plugins/loader.py
import importlib.util, tomllib, logging
from pathlib import Path

log = logging.getLogger("retromanager.plugins")

PLUGIN_DIR = Path.home() / ".config" / "retromanager" / "plugins"

class PluginLoader:

    def discover(self) -> list[PluginManifest]:
        manifests = []
        for manifest_path in PLUGIN_DIR.glob("*/plugin.toml"):
            try:
                with open(manifest_path, "rb") as f:
                    data = tomllib.load(f)
                manifests.append(PluginManifest(**data["plugin"],
                    capabilities=data.get("capabilities", {}).get("required", [])))
            except Exception as e:
                log.warning("plugin inválido em %s: %s", manifest_path, e)
        return manifests

    def load(self, plugin_dir: Path) -> EmulatorPlugin | MetadataPlugin | RomSourcePlugin | ExporterPlugin:
        spec = importlib.util.spec_from_file_location(
            plugin_dir.name, plugin_dir / "__init__.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Convenção: todo plugin expõe create_plugin() → instância da classe concreta
        return module.create_plugin()
```

---

#### Fase 3 (v3.0) — Registry comunitário

```python
# Registry = JSON no GitHub com lista de plugins verificados + hash SHA256
REGISTRY_URL = (
    "https://raw.githubusercontent.com/Borussia80/retromanager"
    "/main/plugins/registry.json"
)
# UI na aba Integrações: "Instalar da comunidade"
# Fluxo: listar → selecionar → baixar → verificar SHA256 → extrair em PLUGIN_DIR → ativar
```

**O que NÃO implementar agora:** subprocess isolation (rodar cada plugin num processo separado com IPC JSON-RPC) adiciona latência em cada chamada de metadado e complica debug. Para desktop app instalado pelo próprio usuário, o modelo de confiança é diferente de um marketplace público. Revisar em v3.0 se houver plugins de terceiros desconhecidos.

---

## 5. Memory Management — auditoria e prevenção de leaks

> PyQt6 sofre com leaks silenciosos de QObject, QPixmap e sinais órfãos.
> Uma sessão longa de uso (>1h) pode consumir 2–3× mais memória que o startup.
> Esta seção define padrões defensivos para toda a codebase.

---

### MEM-001 · Regras de ownership de QObject

```python
# ❌ PADRÃO PERIGOSO — QObject sem parent pode vazar
widget = QLabel("texto")   # parent=None, Python pode coletar ou não

# ✅ PADRÃO CORRETO — sempre passar parent explícito
widget = QLabel("texto", parent=self)

# ❌ PERIGOSO — worker movido para thread sem parent definido antes
worker = DownloadWorker(...)          # parent=None no __init__
worker.moveToThread(thread)          # ownership ambíguo

# ✅ CORRETO — parent=None é ok APENAS quando moveToThread é o destino final
# mas garantir deleteLater() no sinal finished
worker.finished.connect(worker.deleteLater)
thread.finished.connect(thread.deleteLater)
```

---

### MEM-002 · QPixmap — evitar retenção desnecessária

```python
# ❌ PERIGOSO — cache de pixmaps sem limite crescendo indefinidamente
_pixmap_cache: dict[str, QPixmap] = {}   # nunca limpo

# ✅ CORRETO — usar QPixmapCache nativo do Qt (tem limite configurável)
from PyQt6.QtGui import QPixmapCache
QPixmapCache.setCacheLimit(51_200)   # 50 MB em kibibytes

def get_pixmap(path: str) -> QPixmap | None:
    px = QPixmap()
    if QPixmapCache.find(path, px):
        return px
    if px.load(path):
        QPixmapCache.insert(path, px)
        return px
    return None
```

---

### MEM-003 · Sinais órfãos — desconectar ao destruir widgets

```python
# ❌ PERIGOSO — lambda captura self; se o widget for destruído
# mas o sinal ainda existir, o lambda mantém referência viva
self.download_panel.retryClicked.connect(
    lambda name: self._retryDownload(name)   # closure com self
)

# ✅ CORRETO — usar método direto (sem closure) ou weakref
self.download_panel.retryClicked.connect(self._retryDownload)

# Para desconexão explícita no closeEvent ou ao trocar de plataforma:
def _disconnect_platform_signals(self):
    try:
        self._detail_panel.downloadRequested.disconnect()
        self._detail_panel.favoriteToggled.disconnect()
    except (RuntimeError, TypeError):
        pass   # já desconectado — seguro ignorar
```

---

### MEM-004 · Referências circulares — usar weakref em callbacks

```python
# ❌ PERIGOSO — EventBus retém referência forte para self
EventBus.get().download_completed.connect(self._on_completed)
# → se MainWindow for destruído, EventBus ainda tem referência → leak

# ✅ CORRETO — desconectar no closeEvent
def closeEvent(self, event):
    bus = EventBus.get()
    bus.download_completed.disconnect(self._on_completed)
    bus.favorite_changed.disconnect(self._refresh_favorite_indicator)
    super().closeEvent(event)
```

---

### MEM-005 · Auditoria periódica com objgraph no ciclo de dev

```python
# Adicionar como teste de integração (não unitário — requer Qt)
# tests/integration/test_memory.py

def test_platform_navigation_no_leak(qtbot):
    """Navegar entre 5 plataformas não deve aumentar QTableWidgetItem count."""
    import objgraph
    window = MainWindow(mock_settings, mock_updater, mock_platforms)
    qtbot.addWidget(window)

    baseline = objgraph.count("QTableWidgetItem")
    for _ in range(5):
        window._onListwidgetSelectionChanged(some_platform_item)
        qtbot.wait(100)

    final = objgraph.count("QTableWidgetItem")
    assert final <= baseline + 10   # tolerância mínima
```

---

---

### OBS-001 · Structured logging já está bem encaminhado — pequenas melhorias

```python
# _logging.py — adicionar handler para stdout em modo debug
if os.environ.get("DEBUG", "0") != "0":
    stream_h = logging.StreamHandler()
    stream_h.setLevel(logging.DEBUG)
    stream_h.setFormatter(formatter)
    root.addHandler(stream_h)
```

---

### OBS-002 · Crash reporter

```python
# _bootstrap.py
import sys, traceback, logging

def _excepthook(exc_type, exc_value, exc_tb):
    log = logging.getLogger("retromanager.crash")
    log.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
    # Mostrar dialog amigável antes de fechar
    from ui.dialogs.crash_dialog import CrashDialog
    dlg = CrashDialog(traceback.format_exception(exc_type, exc_value, exc_tb))
    dlg.exec()
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _excepthook
```

---

### OBS-003 · Health check da base de dados na inicialização

```python
# _platforms.py — PlatformsHelper.__init__
def _integrity_check(self):
    row = self._db.execute("PRAGMA integrity_check").fetchone()
    if row and row[0] != "ok":
        log.error("SQLite integrity_check falhou: %s — recriando DB", row[0])
        self._db.close()
        Path(PLATFORMS_CACHE_DB).unlink(missing_ok=True)
        self._db = sqlite3.connect(PLATFORMS_CACHE_DB, check_same_thread=False)
        self._db.executescript(_SCHEMA)
```

---

## 6. Engenharia de qualidade — SPRINT 4

---

### ENG-001 · Tipagem estrita com mypy

Adicionar ao projeto:

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["PyQt6-stubs"]
ignore_missing_imports = true   # para módulos sem stubs

[tool.ruff]
target-version = "py312"
select = ["E", "W", "F", "I", "UP", "B", "C4", "SIM"]

[tool.black]
line-length = 100
target-version = ["py312"]
```

---

### ENG-002 · Testes automatizados

```
tests/
├── conftest.py            (fixtures: temp_dir, in-memory DB, mock settings)
├── core/
│   ├── test_library.py    (rom_matches_filters, find_rom_file, scan_downloaded)
│   ├── test_favorites.py  (toggle, is_favorite, all, count)
│   ├── test_history.py    (record, recent, count)
│   ├── test_settings.py   (get, update, write/_read, recovery de EOFError)
│   └── test_catalog.py    (getRom, getRoms, getRomsCount)
├── integrations/
│   ├── test_retroarch.py  (core_path, add_to_playlist, _empty_playlist)
│   └── test_updater.py    (updateAvailable com mock de QNetworkAccessManager)
└── workers/
    └── test_download.py   (DownloadWorker com servidor HTTP mock, hash validation)
```

**Exemplo de teste crítico:**

```python
# tests/core/test_settings.py
def test_read_eofError_uses_defaults(tmp_path, monkeypatch):
    """EOFError não deve crashar; deve usar settings padrão."""
    settings_file = tmp_path / "settings.json"
    settings_file.write_bytes(b"")   # arquivo vazio → EOFError no json.load
    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))
    s = SettingsHelper()
    assert s.get("cache_expiration") == 30   # padrão

def test_read_renamed_key_triggers_fix(tmp_path, monkeypatch):
    """Chave renomeada deve acionar _fix(), não aceitar dict com chave errada."""
    cfg = {"cache_expiration": 7, "old_key": "value",
           "download_path": "/tmp", "import_paths": [],
           "organize_by_platform": True, "unzip": True}
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps(cfg))
    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))
    # Não deve levantar KeyError/ValueError
    s = SettingsHelper()
    assert s.get("cache_expiration") == 7
```

---

### ENG-003 · CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: black --check .
      - run: mypy retromanager/
      - run: pytest tests/ -v --tb=short

  build-appimage:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/build_appimage.sh
      - uses: actions/upload-artifact@v4
        with: { name: RetroManager-AppImage, path: dist/*.AppImage }
```

---

## 7. Distribuição — SPRINT 5

---

### DIST-001 · AppImage com PyInstaller

```bash
# scripts/build_appimage.sh
pyinstaller app.spec --clean --noconfirm
linuxdeploy --appdir dist/AppDir \
    --executable dist/retromanager \
    --desktop-file retromanager.desktop \
    --icon-file resources/icons/icon_256.png \
    --output appimage
```

---

### DIST-002 · Flatpak manifest

```yaml
# org.retromanager.RetroManager.yml
app-id: org.retromanager.RetroManager
runtime: org.gnome.Platform
runtime-version: '46'
sdk: org.gnome.Sdk
command: retromanager
finish-args:
  - --share=network
  - --share=ipc
  - --socket=x11
  - --socket=wayland
  - --filesystem=home
  - --device=dri
modules:
  - name: retromanager
    buildsystem: simple
    build-commands:
      - pip install --prefix=/app .
```

---

## 8. Checklist de aceite v2.2

> Cada item deve estar verde antes do release.

### Sprint 0 — Correções críticas
- [x] BUG-001 · `import requests` no topo de `_tools.py`
- [x] BUG-002 · `selectionModel().selectionChanged.connect(…)` em `download_queue.py`
- [x] BUG-003 · Comparação por `UserRole+3` em `_onDownloadCompletedItem` e `_toggleFavorite`
- [x] BUG-004 · Badge ✓ medido antes do loop de tags em `GameTitleDelegate`
- [x] BUG-005 · `_current_platform()` chamado uma única vez por método
- [x] BUG-006 · `EOFError` logado e tratado em `SettingsHelper._read()`
- [x] BUG-007 · Comparação de chaves por `set()`, não por `len()`
- [x] BUG-008 · `updateAvailable()` verifica `REVISION`
- [x] BUG-009 · `threading.Lock` em `PlatformsHelper` e `HistoryManager`
- [x] BUG-010 · Classe `_Worker` morta removida de `mainwindow.py`

### Sprint 1 — Refatorações
- [x] REF-001 · `@staticmethod` em `Tools` e `DebugHelper`
- [x] REF-002 · `SettingsHelper.get/update` sem loop linear
- [x] REF-003 · Import de `Tools` no topo de `rom_detail_panel.py`
- [x] REF-004 · YAML gerado via `yaml.dump()` em `lutris_helper.py`
- [x] REF-005 · Wildcard imports eliminados de `mainwindow.py` e `download_queue.py`
- [x] REF-006 · `_RomFilterProxy` usa `rom_matches_filters()` (fuzzy consistente)
- [x] REF-007 · `_empty_playlist` — remover ou usar parâmetro `db_name`
- [x] REF-008 · `getPlatformName`/`getRomName` com `LIMIT 1 OFFSET n`

### Sprint 2 — Features
- [x] FEAT-001 · Download engine com concorrência configurável e retry
- [x] FEAT-002 · Busca FTS5 no SQLite
- [ ] FEAT-003 · `RomTableModel` virtual (sem `QTableWidget`) — adiado (alto risco)
- [ ] FEAT-004 · Pelo menos um provider de metadados (ScreenScraper) — adiado (requer credenciais externas)
- [x] FEAT-005 · Smart Collections (Baixados)
- [x] FEAT-006 · Notificações nativas `notify-send`
- [x] FEAT-007 · Suporte a tema claro / sistema
- [x] FEAT-008 · Interfaces abstratas de plugin (`EmulatorPlugin`, `MetadataPlugin`, `RomSourcePlugin`, `ExporterPlugin`)
- [x] FEAT-009 · RetroArch e Lutris migrados para implementações de `EmulatorPlugin`

### Sprint 3 — Observabilidade
- [x] OBS-001 · Logging para stdout em modo debug
- [x] OBS-002 · Crash reporter com dialog amigável
- [x] OBS-003 · `PRAGMA integrity_check` na inicialização do DB

### Sprint PERF — Profiling (executar antes do Sprint 2)
- [x] PERF-001 · `StartupTimer` instrumentado em `_bootstrap.py`; baseline medido e logado
- [ ] PERF-002 · Flame graph gerado com `py-spy`; top-5 hotspots identificados
- [x] PERF-003 · `tracemalloc` + `objgraph` sem crescimento em 10 navegações de plataforma
- [x] PERF-004 · `GameTitleDelegate.paint` < 500 µs por célula confirmado

### Memory Management
- [ ] MEM-001 · Todos os `QObject` criados com `parent` explícito ou `deleteLater()` conectado
- [ ] MEM-002 · `QPixmapCache` com limite de 50 MB substituindo dicts manuais de pixmap
- [ ] MEM-003 · Sinais desconectados explicitamente no `closeEvent` e ao trocar plataforma
- [ ] MEM-004 · `EventBus` desconectado no `closeEvent` do `MainWindow`
- [ ] MEM-005 · Teste de integração `test_platform_navigation_no_leak` verde no CI

### Sprint 4 — Engenharia
- [ ] ENG-001 · `ruff`, `black`, `mypy --strict` passando no CI
- [ ] ENG-002 · Cobertura de testes ≥ 80% em `core/` e `integrations/`
- [ ] ENG-003 · GitHub Actions: lint + test + build AppImage em todo PR

### Sprint 5 — Distribuição
- [ ] DIST-001 · AppImage funcional gerado pelo CI
- [ ] DIST-002 · Flatpak manifest validado com `flatpak-builder`

---

## 9. Referências técnicas

| Recurso | URL |
|---|---|
| PyQt6 docs | https://www.riverbankcomputing.com/static/Docs/PyQt6/ |
| Qt6 threading | https://doc.qt.io/qt-6/thread-support.html |
| SQLite FTS5 | https://www.sqlite.org/fts5.html |
| ScreenScraper API | https://www.screenscraper.fr/webapi2.php |
| Libretro thumbnails | https://thumbnails.libretro.com |
| AppImage | https://appimage.org |
| Flatpak | https://docs.flatpak.org |
| py7zr | https://py7zr.readthedocs.io |

---

*Gerado em 2026-05-15 · Base analisada: RetroManager v2.1.0 · 28 arquivos Python*
