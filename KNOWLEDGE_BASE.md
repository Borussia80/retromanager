# retromanager — Knowledge Base

> Formato: **Karpathy LLM Kiwi** × **AgentMemory**
> Cada seção é um átomo autossuficiente — leia só o que precisar.
> Atualizado: 2026-05-19 · v2.3.12

---

## 📌 Snapshot do Projeto

| Campo | Valor |
|-------|-------|
| Nome | retromanager |
| Tipo | Desktop Linux (PyQt6) |
| Propósito | Navegar e baixar ROMs retro do Archive.org; integra RetroArch/Lutris |
| Versão atual | v2.3.12 |
| Versão alvo | v2.4.0 (refactor arquitetural) |
| Linguagem | Python 3.14 |
| UI | PyQt6 |
| DB | SQLite (FTS5) via `_platforms.py` |
| Empacotamento | AppImage (PyInstaller + appimagetool) + Flatpak |
| Repositório | `git@github.com:Borussia80/retromanager.git` (branch: main) |
| Path local | `/home/rmilet/Trabalho/Projetos/retromanager` |
| Entrada | `app.pyw` / `./run.sh` |
| Testes | `python -m pytest tests/ -q --ignore=tests/integration/test_memory.py` (111 testes) |

---

## 🏗️ Arquitetura Atual

```
app.pyw
 └── MainWindow (mainwindow.py — 1725 linhas, God Class ← PROBLEMA)
      ├── DownloadEngine       (download_engine.py)   QThreadPool + QRunnable
      ├── DownloadQueue        (download_queue.py)    fila persistente em JSON
      ├── DownloadQueuePanel   (download_panel.py)    UI do painel de progresso
      ├── PlatformsHelper      (_platforms.py)        SQLite + FTS5
      ├── ThumbnailFetcher     (thumbnail_cache.py)   QRunnable + urllib
      ├── UpdaterHelper        (_updater.py)          GitHub API + auto-update AppImage
      ├── GameGridWidget       (game_grid.py)         grade de ROMs com QListView
      ├── RomDetailPanel       (rom_detail_panel.py)  painel lateral de detalhes
      ├── FavoritesManager     (favorites_manager.py)
      ├── HistoryManager       (history_manager.py)
      ├── RetroArchHelper      (retroarch_helper.py)
      └── LutrisHelper         (lutris_helper.py)
```

### Módulos sem testes (lacuna crítica)
`mainwindow.py`, `download_engine.py`, `download_panel.py`, `download_queue.py`,
`game_grid.py`, `rom_detail_panel.py`, `_updater.py`

---

## 🧠 Decisões Arquiteturais (ADRs)

### ADR-001 · QThreadPool + QRunnable para downloads
**Decisão:** `DownloadEngine` usa `QThreadPool` + `QRunnable` em vez de `QThread` manual por ROM.
**Por quê:** QThread manual exige gerenciar ciclo de vida manualmente. Python GC destrói
objetos Qt antes do thread C++ terminar → `QThread: Destroyed while thread is still running`.
Com QThreadPool o pool é dono do ciclo de vida; sem GC crashes por design.
**Padrão:** `setAutoDelete(False)` + `self._tasks: set` para manter refs Python vivas.
**Não fazer:** criar `QThread` por ROM; não armazenar ref → GC crash garantido.

### ADR-002 · urllib em QRunnable, não QNetworkAccessManager
**Decisão:** `ThumbnailFetcher.run()` usa `urllib.request.urlopen`, não `QNetworkAccessManager`.
**Por quê:** QThreadPool threads não têm event loop próprio. `QNetworkAccessManager.get()`
em thread sem event loop retorna `QNetworkReply` já deletada → `RuntimeError: wrapped C/C++
object has been deleted`. `urllib` é I/O síncrono bloqueante — correto para QRunnable.
**Regra:** em `QRunnable`, usar I/O síncrono (urllib, requests, sqlite3 direto).
Reservar `QNetworkAccessManager + QEventLoop` para `QThread` com event loop ativo.

### ADR-003 · Sinal `progress` carrega `rom_name`
**Decisão:** `DownloadEngine.progress = pyqtSignal(str, int, int, float)` — primeiro arg é `rom_name`.
**Por quê:** Com 3 downloads concorrentes, o padrão `_active_rom_name` no MainWindow era
sobrescrito a cada `startedItem` — o painel atualizava sempre o último ROM iniciado.
**Não fazer:** usar variável de instância como proxy para identificar qual slot está progredindo.

### ADR-004 · Pseudo-plataformas leem plataforma real do UserRole
**Decisão:** Em views pseudo-plataforma (Favoritos, Recentes, Baixados), a plataforma real
é lida de `item.data(Qt.ItemDataRole.UserRole)` por linha, não do item selecionado na sidebar.
**Por quê:** A sidebar mostra `_FAVORITES_KEY`, não a plataforma real. Usar o key pseudo
como platform → "ROM não encontrada no catálogo".

### ADR-005 · FTS5 tokens escapados antes do MATCH
**Decisão:** `safe_tokens = [t.replace('"', '""') for t in tokens]` antes de montar query FTS5.
**Por quê:** Aspas ou caracteres especiais na query causam `sqlite3.OperationalError`.
Duplas aspas é o escape padrão do SQLite FTS5 dentro de frases quoted.

### ADR-006 · Auto-update AppImage via os.execv
**Decisão:** Auto-update detecta `APPIMAGE` env var; baixa com streaming (readyRead),
rename atômico no mesmo filesystem, `os.execv` para restart.
**Por quê:** `os.execv` substitui o processo atual sem criar processo filho — sem PID duplo,
sem zombie. Rename atômico garante que nunca há AppImage corrompido em disco.
**Fallback:** se não rodando como AppImage (dev mode), abre navegador.

---

## 🐛 Padrões de Bug e Root Causes

### PADRÃO-001 · `QThread: Destroyed while thread is still running`
**Causa raiz:** Python GC destrói objeto QThread/QWorker enquanto thread C++ ainda roda.
Triggers: ref só em dict local, retry timer sobrescreve ref, `pop` antes de thread terminar.
**Fix permanente:** QThreadPool (`setAutoDelete(False)` + set de refs Python).
**Anti-padrão:** `_active_threads[rom_name] = thread` sobrescrito no retry antes de terminar.

### PADRÃO-002 · `RuntimeError: wrapped C/C++ object ... has been deleted`
**Causa raiz:** objeto Qt deletado pelo C++ antes do Python tentar acessá-lo.
Contexts: QNetworkReply em QRunnable thread (sem event loop), QRunnable com `setAutoDelete(True)`
conectado a slots que rodam depois do pool liberar o objeto.
**Fix:** manter ref Python explícita; em QRunnable usar urllib, não QNAM.

### PADRÃO-003 · Thumbnails não aparecem
**Causa raiz histórica 1 (v2.3.8):** `ThumbnailFetcher` com `setAutoDelete(True)` — GC destrói
`fetcher.signals` após `pool.start(fetcher)`, cortando conexões de sinal.
**Fix:** `_active_fetchers: set` no `GameGridWidget`; discard nos slots done/failed.
**Causa raiz histórica 2 (v2.3.12):** `QNetworkAccessManager` em QRunnable thread (ADR-002).
**Fix:** substituir por `urllib.request.urlopen`.

### PADRÃO-004 · "ROM não encontrada no catálogo" em Favoritos/Recentes
**Causa raiz:** `_addToQueue` usava o item da sidebar (pseudo-key) como plataforma.
**Fix:** `it.data(Qt.ItemDataRole.UserRole)` por linha para obter plataforma real.

---

## 📦 Catálogo de Plataformas (Archive.org IDs)

| Plataforma | Formato | Source IDs |
|-----------|---------|-----------|
| Nintendo NES | zip | `no-intro-nes-roms-from-myrient-*` (5 partes) |
| Nintendo SNES | zip | `ef_nintendo_snes_no-intro_2024-04-20` |
| Nintendo 64 | zip | `ef_nintendo_64_no-intro_2024-02-10` |
| Nintendo GameBoy | zip | `theentiregameboycollection` |
| Nintendo GBA | zip | `theentiregameboyadvancecollection` |
| Sega Megadrive | 7z | `nointro.md` |
| Sega Master System | 7z | `nointro.ms-mkiii` |
| Sega Game Gear | 7z | `nointro.gg` |
| Atari 2600 | 7z | `nointro.atari-2600` |
| SNK Neo Geo MVS | zip | `neo-geo-mvs-romset` |
| Arcade MAME | zip | `mame-merged` (subdir `mame-merged/`) |
| Sony PlayStation | zip | `2024-sony-playstation-{usa,eur,jap}-hearto-1g1r-collection` |
| Sony PS2 | chd | `sony-playstation-2-{letter}-redump-collection` (30 partes) |
| Sony PSP | chd | `psp-chd-zstd-redump-part{1,2}` |

**Atenção PS2:** format field no Archive.org é `Unknown`; detecção feita por extensão `.chd`.

---

## 🔄 Fluxo de Release (OBRIGATÓRIO — nunca pular etapas)

```bash
# 1. Bump version
# editar _constants.py: VERSION_REVISION += 1

# 2. Commit + push
git add -p && git commit -m "chore(release): bump version to vX.Y.Z"
git push origin main

# 3. GitHub release
gh release create vX.Y.Z --title "vX.Y.Z" --notes "..."

# 4. Build AppImage
bash packaging/build_appimage.sh
# → gera retromanager-X.Y.Z-x86_64.AppImage na raiz

# 5. Upload binário (OBRIGATÓRIO — sem isso o release está incompleto)
gh release upload vX.Y.Z retromanager-X.Y.Z-x86_64.AppImage --clobber
```

**Por quê é obrigatório:** o AppImage é o único artefato que usuários Linux executam
diretamente. Release sem binário = release inútil.

---

## 🗺️ Roadmap v2.4.0 — Refactor `mainwindow.py`

**Problema:** 1725 linhas / 75 métodos — God Class, viola SOLID-S, impede testes de UI.

**Arquitetura alvo:**
```
MainWindow (orquestrador fino, < 300 linhas)
  ├── UpdateController     (~6 métodos — check, download, install, restart)
  ├── DownloadController   (~12 métodos — engine, thread, painel, retry)
  ├── CatalogController    (~10 métodos — filtros, busca FTS, tabela)
  └── LibraryController    (~8 métodos — favoritos, histórico, importação)
```

**Fases e versões:**

| Fase | Controlador | Versão | Status |
|------|------------|--------|--------|
| 0 | Preparação (QThreadPool, thumbnails, FTS5) | v2.3.x | ✅ Concluído |
| 1 | `UpdateController` | v2.3.13 | ⬜ Próximo |
| 2 | `DownloadController` | v2.3.13 | ✅ Concluído |
| 3 | `CatalogController` | v2.3.14 | ⬜ |
| 4 | `LibraryController` | v2.3.15 | ⬜ |
| 5 | Finalização (ruff, mypy, cov 80%, release) | v2.4.0 | ⬜ |

**Regra de sessão:** uma fase por sessão. Só parar com testes passando + commit feito.

---

## ⚙️ Configuração do Ambiente

```bash
# Dependências
pip install PyQt6 requests pyinstaller ruff

# Rodar
./run.sh                          # ou .venv/bin/python app.pyw

# Testes
python -m pytest tests/ -q --ignore=tests/integration/test_memory.py

# Linting
python -m ruff check .
python -m ruff check . --fix      # 51 erros auto-fixáveis

# Build AppImage
bash packaging/build_appimage.sh

# Checar processo ativo
pgrep -a python | grep app.pyw
```

**Config dir:** `~/.config/retromanager/settings.json`
**Cache dir:** `~/.cache/retromanager/` (thumbnails + DB SQLite)
**Download default:** `~/ROMs/`

---

## 🔬 Módulos Principais — Interface Pública

### `DownloadEngine` (download_engine.py)
```python
engine = DownloadEngine(settings, platforms, [("Nintendo - NES", "rom_name")], max_concurrent=3)
engine.startedItem.connect(...)    # (platform, rom_name, slot, total)
engine.progress.connect(...)       # (rom_name, bytes_done, total_bytes, speed)
engine.completedItem.connect(...)  # (platform, rom_name)
engine.failedItem.connect(...)     # (platform, rom_name, error)
engine.finished.connect(...)
engine.run()
engine.cancel()
```
**Interno:** `_DownloadTask(QRunnable)` com `_Signals(QObject)` — padrão obrigatório
para emitir sinais de QRunnable (QRunnable não herda de QObject).

### `PlatformsHelper` (_platforms.py)
```python
ph = PlatformsHelper()
ph.platformsCount()                         # int
ph.getPlatforms()                           # generator de nomes
ph.getRomsCount(platform_name)              # int
ph.search_roms(platform_name, query, 500)   # list[str] — FTS5 com fallback Python
ph.getRom(platform_name, rom_name)          # RomEntry | None
ph.getRoms(platform_name)                   # generator (name, RomEntry)
```
**FTS5:** tokens escapados (`"` → `""`) antes do MATCH. Fallback Python com `rom_matches_filters`.

### `ThumbnailFetcher` (thumbnail_cache.py)
```python
fetcher = ThumbnailFetcher(platform, rom_name)
fetcher.signals.done.connect(...)    # (platform, rom_name, local_path)
fetcher.signals.failed.connect(...)  # (platform, rom_name)
QThreadPool.globalInstance().start(fetcher)
# IMPORTANTE: manter ref em set até done/failed para evitar GC
```

### `UpdaterHelper` (_updater.py)
```python
u = UpdaterHelper()
u.updateAvailable()        # bool — faz fetch da API do GitHub
u.latestAppImageUrl()      # str — URL do asset .AppImage do último release
u.currentVersionString()   # "v2.3.12"
u.latestVersionString()    # "v2.3.X"
```

---

## 🚨 Anti-padrões Documentados

| Anti-padrão | Consequência | Alternativa |
|------------|-------------|-------------|
| `QThread` manual por ROM | GC crash, `Destroyed while running` | `QThreadPool + QRunnable` |
| `QNetworkAccessManager` em `QRunnable.run()` | `wrapped C/C++ deleted` | `urllib.request.urlopen` |
| `setAutoDelete(True)` + conectar sinais após `pool.start()` | GC destrói `signals` | `setAutoDelete(False)` + set de refs |
| `_active_rom_name` para rastrear progresso paralelo | painel atualiza ROM errado | `rom_name` no próprio sinal |
| Sidebar pseudo-key como platform em `_addToQueue` | "ROM não encontrada" | `item.data(UserRole)` por linha |
| FTS5 query com user input não-escapado | `OperationalError` | `t.replace('"', '""')` |
| `except Exception: pass` silencioso | bugs ocultos em produção | captura específica + `_log.error(...)` |
| Commit sem AppImage upload | release inútil | sempre executar passo 5 do release |

---

## 📝 Histórico de Versões (Resumido)

| Versão | Data | Destaque |
|--------|------|---------|
| v2.0.0 | 2026-03-20 | SQLite, QNetworkAccessManager, AppImage/Flatpak |
| v2.1.0 | 2026-04-10 | Histórico recente, fuzzy search, retry ETA |
| v2.3.0 | 2026-04-28 | Sony PS/PS2/PSP, FTS5, temas, 97 testes, CI |
| v2.3.6 | 2026-05-18 | Fix crash `QRect→QRectF` no game grid |
| v2.3.8 | 2026-05-18 | Fix thumbnails GC, fix pseudo-platform queue |
| v2.3.10 | 2026-05-19 | DownloadEngine reescrito com QThreadPool (KISS) |
| v2.3.11 | 2026-05-19 | progress signal com rom_name, FTS5 escape, delete guard |
| v2.3.12 | 2026-05-19 | Auto-update AppImage integrado, urllib em ThumbnailFetcher |
