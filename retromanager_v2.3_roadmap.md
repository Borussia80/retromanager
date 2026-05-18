# RetroManager v2.3 — Roadmap Técnico

> **Contexto:** v2.2 concluída com 89% (41/46 itens).
> v2.3 dividida em duas releases após revisão colaborativa (Claude + Kimi).

---

## Estrutura de releases

| Release | Prazo | Foco |
|---------|:-----:|------|
| **v2.3.0** | 4–6 semanas | Plataformas Sony + RetroArch "funciona out of the box" |
| **v2.3.1** | +4 semanas | Xbox · Launchers externos · Qualidade arquitetural |

**v2.3.0:** PLAT (Sony) · HEALTH · Schema SQLite · QUAL-002 · QUAL-003

**v2.3.1:** PLAT (Xbox) · LAUNCHER · ADAPTER · QUAL-001

---

## 0. Pendentes herdados da v2.2

| Item | Motivo | Release |
|------|--------|:-------:|
| FEAT-003 · QTableWidget → QAbstractTableModel | Alto risco de regressão | v2.3.1 |
| FEAT-004 · ScreenScraper | Requer credenciais externas | v2.4 |
| PERF-002 · Flame graph py-spy | Medição manual | v2.3.0 |
| MEM-005 · test_platform_navigation_no_leak | Requer pytest-qt | v2.3.0 |

---

## 1. SPRINT PLAT — Plataformas Sony e Microsoft

> ⚠️ **Pré-requisito:** HEALTH deve estar ativo antes de PS1/PS2 aparecerem
> na sidebar. Sem HealthCheck, o usuário baixa ROMs que não rodam sem
> saber o motivo.

### Escopo v2.3.0 — apenas Sony

| Plataforma | Prioridade | Observação |
|------------|:----------:|------------|
| Sony - PlayStation 1 | Alta | Core maduro, Archive.org público |
| Sony - PlayStation 2 | Alta | Core PCSX2 beta funcional |
| Sony - PSP | Alta | Core PPSSPP estável |
| Sony - PlayStation 3 | Baixa | Launcher-only via RPCS3 — ver fluxo abaixo |

> Microsoft - Xbox movido para v2.3.1 — ISOs de 8 GB, xemu ainda
> madurando, simplifica o HealthCheck desta sprint.
> Microsoft - Xbox 360 fora do escopo — Xenia instável; jogos vendidos digitalmente.

### Alterações necessárias

**`_constants.py`**
```python
['Sony - PlayStation',   'chd', 'no-intro_sony_playstation_chd'],
['Sony - PlayStation 2', 'chd', 'redump-sony-playstation2-chd'],
['Sony - PSP',           'zip', 'nointro.psp'],
# Microsoft - Xbox: adicionado na v2.3.1
```

**`retroarch_helper.py`**
```python
# CORE_MAP
"Sony - PlayStation":   ("mednafen_psx_hw_libretro.so", "Beetle PSX HW"),
"Sony - PlayStation 2": ("pcsx2_libretro.so",           "PCSX2"),
"Sony - PSP":           ("ppsspp_libretro.so",          "PPSSPP"),

# SYSTEM_MAP
"Sony - PlayStation":   "Sony - PlayStation",
"Sony - PlayStation 2": "Sony - PlayStation 2",
"Sony - PSP":           "Sony - PlayStation Portable",
```

**`platform_icons.py`**
```python
"Sony - PlayStation":   {"abbr": "PS1", "color": "#003791"},
"Sony - PlayStation 2": {"abbr": "PS2", "color": "#00439c"},
"Sony - PSP":           {"abbr": "PSP", "color": "#003087"},
"Sony - PlayStation 3": {"abbr": "PS3", "color": "#001f6e"},
# Microsoft - Xbox: adicionado na v2.3.1
```

**`thumbnail_cache.py`**
```python
"Sony - PlayStation":   "Sony - PlayStation",
"Sony - PlayStation 2": "Sony - PlayStation 2",
"Sony - PSP":           "Sony - PlayStation Portable",
"Sony - PlayStation 3": "Sony - PlayStation 3",
# Microsoft - Xbox: adicionado na v2.3.1
```

### Aviso de arquivo grande

PS2 CHDs chegam a 4 GB. Adicionar em `RomDetailPanel._on_download()`:

```python
def _on_download(self):
    if not (self._platform and self._rom_name):
        return
    if self._rom_size and self._rom_size > 1_000_000_000:   # guard: size pode ser None/0
        reply = QMessageBox.question(
            self, "Arquivo grande",
            f"Este arquivo tem {Tools.convertSizeToReadable(self._rom_size)}.\n"
            "Deseja continuar o download?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
    self.downloadRequested.emit(self._platform, self._rom_name)
```

### Plugin RPCS3 (PS3)

> **Fluxo launcher-only:** PS3 não tem catálogo de download no RetroManager
> (decisão legal). O usuário fornece a ROM por conta própria. O RetroManager
> escaneia a pasta configurada, exibe o jogo na sidebar e lança via RPCS3.
> Como `add_to_library` retorna `False`, a ROM não entra na biblioteca
> interna — aparece apenas se a pasta for adicionada como "pasta de importação"
> nas opções. Documentar isso claramente na UI de configuração do plugin.

```python
# plugins/rpcs3/__init__.py
import shutil
import subprocess
from pathlib import Path
from core.plugins.base import EmulatorPlugin


class RPCS3Plugin(EmulatorPlugin):

    @property
    def name(self) -> str:
        return "RPCS3"

    def detected(self) -> bool:
        return bool(
            shutil.which("rpcs3") or
            Path.home().joinpath(
                ".local/share/flatpak/exports/bin/net.rpcs3.RPCS3"
            ).exists()
        )

    def launch(self, platform: str, rom_path: str) -> bool:
        exe = shutil.which("rpcs3") or "rpcs3"
        # RPCS3 precisa do EBOOT.BIN dentro da estrutura do jogo
        eboot = next(Path(rom_path).rglob("EBOOT.BIN"), None)
        subprocess.Popen([exe, "--no-gui", str(eboot or rom_path)])
        return True

    def add_to_library(self, platform: str, rom_name: str, rom_path: str) -> bool:
        return False   # RPCS3 gerencia biblioteca internamente


def create_plugin() -> RPCS3Plugin:
    return RPCS3Plugin()
```

---

## 2. SPRINT LAUNCHER — Integração com Launchers

> RetroManager resolve a parte difícil. O usuário joga de onde preferir.

### Prioridade

| Launcher | Prioridade |
|----------|:----------:|
| Steam | Alta — maior base Linux; Steam Deck |
| Pegasus | Alta — muito usado no Linux |
| EmulationStation DE | Média |
| Lutris | Existente — manter como está |

### Interface comum (já existe da v2.2)

```python
# core/plugins/base.py
class ExporterPlugin(ABC):
    @abstractmethod
    def export(self, roms: list[tuple[str, str]], output_dir: str) -> bool: ...

    @abstractmethod
    def format_name(self) -> str: ...
```

### LAUNCH-001 · Steam

Steam armazena shortcuts em `~/.steam/root/userdata/<id>/config/shortcuts.vdf` (binário).

```python
# integrations/exporters/steam.py
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import steam.shortcuts as sc   # pip install steam-shortcut-editor
from PyQt6.QtWidgets import QMessageBox
from core.plugins.base import ExporterPlugin


class SteamShortcutExporter(ExporterPlugin):

    def __init__(self, retroarch, settings):
        self._ra = retroarch
        self._settings = settings

    def format_name(self) -> str:
        return "Steam"

    def detected(self) -> bool:
        return self._shortcuts_path() is not None

    def export(self, roms: list[tuple[str, str]], output_dir: str) -> bool:
        path = self._shortcuts_path()
        if not path:
            return False

        # Escrita concorrente com Steam aberto pode corromper o VDF
        if self._steam_running():
            reply = QMessageBox.warning(
                None, "Steam aberto",
                "Feche o Steam antes de exportar para evitar corrupção.\n"
                "Deseja continuar mesmo assim?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return False

        self._backup(path)

        shortcuts = sc.read_shortcuts(str(path))
        existing = {s.get("AppName") for s in shortcuts}

        for platform, rom_name in roms:
            if rom_name in existing:
                continue
            rom_path = self._find_rom(platform, rom_name)
            if not rom_path:
                continue
            core = self._ra.core_path(platform)
            exe = self._ra.exe or "retroarch"
            args = f'-L "{core}" "{rom_path}"' if core else f'"{rom_path}"'
            shortcuts.append({
                "AppName": rom_name,
                "Exe": exe,
                "StartDir": str(Path(rom_path).parent),
                "LaunchOptions": args,
                "IsHidden": False,
                "AllowDesktopConfig": True,
                "OpenVR": False,
                "tags": {0: platform},
            })

        sc.write_shortcuts(shortcuts, str(path))
        return True

    def _shortcuts_path(self) -> Path | None:
        root = Path.home() / ".steam" / "root" / "userdata"
        if not root.exists():
            return None
        for user_dir in root.iterdir():
            candidate = user_dir / "config" / "shortcuts.vdf"
            if candidate.exists():
                return candidate
        return None

    def _steam_running(self) -> bool:
        return subprocess.run(
            ["pgrep", "-x", "steam"], capture_output=True
        ).returncode == 0

    def _backup(self, path: Path) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, path.with_suffix(f".vdf.bak_{ts}"))

    def _find_rom(self, platform: str, rom_name: str) -> str | None:
        from library_service import find_rom_file
        return find_rom_file(self._settings, rom_name, platform)
```

### LAUNCH-002 · Pegasus

```python
# integrations/exporters/pegasus.py
from pathlib import Path
from core.plugins.base import ExporterPlugin


class PegasusExporter(ExporterPlugin):

    def __init__(self, retroarch):
        self._ra = retroarch

    def format_name(self) -> str:
        return "Pegasus Frontend"

    def export(self, roms: list[tuple[str, str]], output_dir: str) -> bool:
        by_platform: dict[str, list[str]] = {}
        for platform, rom_name in roms:
            by_platform.setdefault(platform, []).append(rom_name)

        for platform, names in by_platform.items():
            platform_dir = Path(output_dir) / platform
            platform_dir.mkdir(parents=True, exist_ok=True)

            core = self._ra.core_path(platform) or ""
            launch_cmd = (
                f"retroarch -L {core} {{file.path}}" if core
                else "retroarch {file.path}"
            )

            lines = [f"collection: {platform}", f"launch: {launch_cmd}", ""]
            for name in sorted(names):
                lines += [f"game: {name}", f"file: {name}.*", ""]

            (platform_dir / "metadata.pegasus.txt").write_text(
                "\n".join(lines), encoding="utf-8"
            )
        return True
```

### LAUNCH-003 · EmulationStation DE

```python
# integrations/exporters/emulationstation.py
import xml.etree.ElementTree as ET
from pathlib import Path
from core.plugins.base import ExporterPlugin


class EmulationStationExporter(ExporterPlugin):

    def format_name(self) -> str:
        return "EmulationStation DE"

    def export(self, roms: list[tuple[str, str]], output_dir: str) -> bool:
        by_platform: dict[str, list[str]] = {}
        for platform, rom_name in roms:
            by_platform.setdefault(platform, []).append(rom_name)

        for platform, names in by_platform.items():
            platform_dir = Path(output_dir) / platform
            platform_dir.mkdir(parents=True, exist_ok=True)

            root = ET.Element("gameList")
            for name in sorted(names):
                game = ET.SubElement(root, "game")
                ET.SubElement(game, "path").text = f"./{name}.*"
                ET.SubElement(game, "name").text = name
                # Reaproveita thumbnails já cacheados
                thumb = self._thumbnail(platform, name)
                if thumb:
                    ET.SubElement(game, "image").text = thumb

            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(
                str(platform_dir / "gamelist.xml"),
                encoding="utf-8",
                xml_declaration=True,
            )
        return True

    @staticmethod
    def _thumbnail(platform: str, rom_name: str) -> str | None:
        from thumbnail_cache import load_cached_path
        return load_cached_path(platform, rom_name)
```

### UI — aba Exportar Biblioteca

```
┌─ Exportar Biblioteca ──────────────────────────────────────┐
│  ● Steam              Detectado     [Exportar]              │
│  ● Pegasus Frontend   Detectado     [Exportar]              │
│  ◌ EmulationStation   Não instalado [—]                     │
│  ● Lutris             Detectado     [Exportar]              │
│                                                             │
│  ☐ Sincronizar automaticamente após cada download           │
│                              [Exportar todos detectados]    │
└─────────────────────────────────────────────────────────────┘
```

> Sincronização automática deve rodar em thread separada —
> não bloquear o progresso de download na UI.
>
> ⚠️ **Thread safety:** `ExporterPlugin.export()` não é thread-safe por padrão.
> Com downloads paralelos (DownloadEngine max_concurrent=3), múltiplas
> conclusões simultâneas podem tentar escrever no mesmo `shortcuts.vdf`
> ou `metadata.pegasus.txt`. Usar um único worker thread serializado
> para todos os exports automáticos — `QThreadPool` com `maxThreadCount(1)`
> ou uma fila dedicada.

---

## 3. SPRINT HEALTH — RetroArch HealthCheck

> Resolve a dor central: configurar RetroArch falha silenciosamente.
> HealthCheck torna o problema visível e corrigível com um clique.

```python
# core/health.py
import logging
from dataclasses import dataclass, field
from retroarch_helper import RetroArchHelper

log = logging.getLogger("retromanager.health")

BIOS_REQUIRED: dict[str, list[str]] = {
    "Sony - PlayStation":              ["scph5501.bin", "scph5500.bin", "scph5502.bin"],
    "Sony - PlayStation 2":            ["ps2-0230a-20080220.bin"],
    "Sony - PSP":                      [],   # PPSSPP não requer BIOS
    "Nintendo - Famicom Disk":         ["disksys.rom"],
    "NEC - PC Engine / TurboGrafx-16": ["syscard3.pce"],
    "SNK - Neo Geo MVS":               ["neogeo.zip"],
    "Arcade - MAME":                   [],   # BIOS por jogo, não por plataforma
    "Microsoft - Xbox":                ["mcpx_1.0.bin", "Complex_4627.bin"],
}


@dataclass
class PlatformHealth:
    platform: str
    retroarch_found: bool
    core_installed: bool
    core_path: str | None
    core_name: str
    bios_required: list[str] = field(default_factory=list)
    bios_found: list[str]    = field(default_factory=list)
    bios_missing: list[str]  = field(default_factory=list)
    issues: list[str]        = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.retroarch_found and self.core_installed and not self.bios_missing

    @property
    def severity(self) -> str:
        if self.ready:
            return "ok"
        if not self.retroarch_found or not self.core_installed:
            return "error"
        return "warning"   # RetroArch ok, core ok, mas BIOS parcialmente ausente


class RetroArchHealthChecker:

    def __init__(self, retroarch: RetroArchHelper):
        self._ra = retroarch

    def check(self, platform: str) -> PlatformHealth:
        health = PlatformHealth(
            platform=platform,
            retroarch_found=self._ra.detected,
            core_installed=False,
            core_path=None,
            core_name=self._ra.core_name(platform),
            bios_required=BIOS_REQUIRED.get(platform, []),
        )

        if not self._ra.detected:
            health.issues.append("RetroArch não encontrado.")
            return health

        core_path = self._ra.core_path(platform)
        health.core_installed = bool(core_path)
        health.core_path = core_path
        if not health.core_installed:
            health.issues.append(
                f"Core '{health.core_name}' não instalado. "
                "Instale via RetroArch → Núcleos Online."
            )

        bios_dir = self._ra.config_dir / "system" if self._ra.config_dir else None
        for bios_file in health.bios_required:
            if bios_dir and (bios_dir / bios_file).exists():
                health.bios_found.append(bios_file)
            else:
                health.bios_missing.append(bios_file)
                health.issues.append(f"BIOS ausente: {bios_file}")

        return health

    def check_all(self, platforms: list[str]) -> dict[str, PlatformHealth]:
        return {p: self.check(p) for p in platforms}
```

### UI

```
┌────────────────────────────────┐
│ ● PS1        ✅  1.247 itens   │
│ ● PS2        ⚠️    892 itens   │  ← BIOS ausente
│ ● PSP        ✅    634 itens   │
│ ● MAME       ❌  9.841 itens   │  ← core não instalado
└────────────────────────────────┘
```

```
┌─ Diagnóstico — PlayStation 2 ──────────────────────┐
│  ✅  RetroArch detectado                            │
│  ✅  Core PCSX2 instalado                           │
│  ❌  BIOS ausente: ps2-0230a-20080220.bin           │
│                                                     │
│  Coloque a BIOS em:                                 │
│  ~/.config/retroarch/system/                        │
│                                [Abrir pasta] [OK]   │
└─────────────────────────────────────────────────────┘
```

---

## 4. SPRINT ADAPTER — PlatformAdapter

> Não é suporte a Windows agora — é não criar dívida que impeça o
> suporte futuro. Uma tarde de trabalho com benefício permanente.

```python
# core/platform_adapter.py
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path


class PlatformAdapter(ABC):

    @abstractmethod
    def config_dir(self, app: str) -> Path: ...

    @abstractmethod
    def cache_dir(self, app: str) -> Path: ...

    @abstractmethod
    def notify(self, title: str, body: str) -> None: ...

    @abstractmethod
    def open_folder(self, path: str) -> None: ...


class LinuxAdapter(PlatformAdapter):

    def config_dir(self, app: str) -> Path:
        base = os.environ.get("XDG_CONFIG_HOME", "")
        return Path(base) / app if base else Path.home() / ".config" / app

    def cache_dir(self, app: str) -> Path:
        base = os.environ.get("XDG_CACHE_HOME", "")
        return Path(base) / app if base else Path.home() / ".cache" / app

    def notify(self, title: str, body: str) -> None:
        import shutil
        if shutil.which("notify-send"):
            subprocess.Popen(["notify-send", "-a", "RetroManager", title, body])

    def open_folder(self, path: str) -> None:
        subprocess.Popen(["xdg-open", path])


class WindowsAdapter(PlatformAdapter):
    """Stub — não usado na v2.3. Implementar na v3.0 se houver port.
    Métodos levantam NotImplementedError para falhar explicitamente
    em vez de criar paths relativos silenciosos."""

    def config_dir(self, app: str) -> Path:
        raise NotImplementedError("WindowsAdapter não implementado na v2.3")

    def cache_dir(self, app: str) -> Path:
        raise NotImplementedError("WindowsAdapter não implementado na v2.3")

    def notify(self, title: str, body: str) -> None:
        raise NotImplementedError("WindowsAdapter não implementado na v2.3")

    def open_folder(self, path: str) -> None:
        raise NotImplementedError("WindowsAdapter não implementado na v2.3")


# Instância global — importar em vez de instanciar em cada módulo
platform = WindowsAdapter() if sys.platform == "win32" else LinuxAdapter()
```

**Migração:**
```python
# _constants.py — antes
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", APP_NAME)

# _constants.py — depois
from core.platform_adapter import platform
CONFIG_DIR = str(platform.config_dir(APP_NAME))
```

---

## 5. SPRINT QUALITY

### QUAL-001 · QTableWidget → QAbstractTableModel

Feature flag para rollback seguro (v2.3.1):

```python
# _settings.py
use_virtual_table: bool = False

# mainwindow.py
if self._settings.get("use_virtual_table"):
    self._rom_view = RomTableView(self)
else:
    self._rom_view = self.tw_romsList   # legado intacto
```

### QUAL-002 · Flame graph

```bash
py-spy record -o docs/perf/v2.3_profile.svg -- python app.pyw
```

Documentar os 5 hotspots em `docs/perf/v2.3_profile.md` antes de
qualquer otimização. Sem baseline, otimização é chute.

### QUAL-003 · Teste de leak

```bash
pip install pytest-qt objgraph
```

```python
# tests/integration/test_memory.py
def test_platform_navigation_no_leak(qtbot):
    import objgraph
    window = MainWindow(mock_settings, mock_updater, mock_platforms)
    qtbot.addWidget(window)

    baseline = objgraph.count("QTableWidgetItem")
    for _ in range(10):
        for item in platform_items:
            window._onListwidgetSelectionChanged(item)
            qtbot.wait(50)

    assert objgraph.count("QTableWidgetItem") <= baseline + 20
```

---

## 6. Schema SQLite — migração v2

Usa `PRAGMA table_info` para ser idempotente — rodar duas vezes não
quebra nada e não precisa de tabela de controle de versão.

```python
# _platforms.py
def _migrate_v2(self) -> None:
    """Adiciona colunas de metadados. Idempotente."""
    existing = {row[1] for row in self._db.execute("PRAGMA table_info(roms)")}
    if "description" in existing:
        return   # já migrado

    self._db.executescript("""
        ALTER TABLE roms ADD COLUMN description TEXT    NOT NULL DEFAULT '';
        ALTER TABLE roms ADD COLUMN genre       TEXT    NOT NULL DEFAULT '';
        ALTER TABLE roms ADD COLUMN year        INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE roms ADD COLUMN rating      REAL    NOT NULL DEFAULT 0.0;
        ALTER TABLE roms ADD COLUMN cover_url   TEXT    NOT NULL DEFAULT '';
        ALTER TABLE roms ADD COLUMN region      TEXT    NOT NULL DEFAULT '';

        CREATE INDEX IF NOT EXISTS idx_roms_year   ON roms (year);
        CREATE INDEX IF NOT EXISTS idx_roms_rating ON roms (rating);
        CREATE INDEX IF NOT EXISTS idx_roms_region ON roms (region);
    """)
    self._db.commit()

def _rebuild_fts(self) -> None:
    """Re-sincroniza o índice FTS5 com a tabela roms.
    Rebuild incremental — não destrói o índice como DROP/CREATE faria."""
    self._db.execute("INSERT INTO roms_fts(roms_fts) VALUES('rebuild')")
    self._db.commit()
```

Chamar na inicialização, após conectar:
```python
self._migrate_v2()
self._rebuild_fts()
```

---

## 7. Checklist de aceite

### v2.3.0 — PLAT
- [ ] HEALTH ativo antes de PS1/PS2 na sidebar
- [ ] PS1, PS2, PSP em `ARCHIVE_PLATFORMS_DATA` com IDs verificados
- [ ] `CORE_MAP`, `SYSTEM_MAP`, `PLATFORM_STYLE`, `LIBRETRO_SYSTEM` atualizados (sem Xbox)
- [ ] Aviso de arquivo grande com guard `self._rom_size and self._rom_size > 1_000_000_000`
- [ ] Plugin `rpcs3` com fluxo launcher-only documentado na UI de configuração

### v2.3.0 — HEALTH
- [ ] `PlatformHealth` com `ready` e `severity`
- [ ] `BIOS_REQUIRED` para PS1, PS2, FDS, PCE, Neo Geo (Xbox adicionado na v2.3.1)
- [ ] `check()` cobre core, BIOS e RetroArch
- [ ] Ícone ✅/⚠️/❌ na sidebar por plataforma
- [ ] Dialog com "Abrir pasta" para diretório de BIOS
- [ ] Testes unitários com mocks de filesystem

### v2.3.0 — Schema
- [ ] `_migrate_v2()` idempotente (rodar 2x não quebra)
- [ ] `_rebuild_fts()` via `INSERT INTO roms_fts(roms_fts) VALUES('rebuild')`
- [ ] Teste: banco existente migra sem perda de dados

### v2.3.0 — Qualidade
- [ ] QUAL-002: flame graph gerado; top-5 hotspots em `docs/perf/`
- [ ] QUAL-003: `test_platform_navigation_no_leak` verde no CI

### v2.3.1 — PLAT (Xbox)
- [ ] `Microsoft - Xbox` em `ARCHIVE_PLATFORMS_DATA` com ID verificado
- [ ] `CORE_MAP`, `SYSTEM_MAP`, `PLATFORM_STYLE`, `LIBRETRO_SYSTEM` atualizados para Xbox
- [ ] BIOS Xbox (`mcpx_1.0.bin`, `Complex_4627.bin`) adicionadas ao `BIOS_REQUIRED`
- [ ] Plugin `xemu` implementando `EmulatorPlugin`

### v2.3.1 — LAUNCHER
- [ ] Steam: aviso se processo aberto + backup timestamped antes de escrever
- [ ] Steam: shortcuts escritos sem corrupção
- [ ] Pegasus: `metadata.pegasus.txt` com `launch` correto
- [ ] ES-DE: `gamelist.xml` com `<image>` do cache de thumbnails
- [ ] Aba "Exportar Biblioteca" com detecção automática
- [ ] Export automático serializado em single worker thread (`maxThreadCount(1)`)
- [ ] Testes unitários para cada exporter

### v2.3.1 — ADAPTER
- [ ] `LinuxAdapter` XDG-compliant
- [ ] `platform.config_dir()` e `platform.cache_dir()` em `_constants.py`
- [ ] CI falha se encontrar path hardcoded:
  ```bash
  grep -rn "expanduser.*\.config" --include="*.py" src/ && exit 1 || true
  ```
- [ ] `platform.notify()` e `platform.open_folder()` substituindo chamadas diretas

### v2.3.1 — QUAL-001
- [ ] Feature flag `use_virtual_table = False` no settings
- [ ] `RomTableModel` testado com 40k+ itens
- [ ] Scroll MAME mantém 60 FPS com modelo virtual

---

## 8. Metas de performance

| Métrica | v2.2 | Meta v2.3 |
|---------|:----:|:---------:|
| Startup cold | < 2s | < 1.5s |
| Busca FTS5 | < 50ms | < 30ms |
| Scroll MAME 40k | 60 FPS | 60 FPS mantido |
| HealthCheck por plataforma | N/A | < 200ms |
| Export Steam 500 ROMs | N/A | < 2s |
| Footprint idle | < 80 MB | < 70 MB |

---

## 9. Referências

| Recurso | URL |
|---------|-----|
| Steam shortcuts VDF | https://github.com/CorporalQuesadilla/Documentation/blob/master/Steam/Steam%20Custom%20Shortcuts%20Documentation.md |
| steam-shortcut-editor | https://pypi.org/project/steam-shortcut-editor |
| Pegasus metadata | https://pegasus-frontend.org/docs/user-guide/meta-files |
| ES-DE gamelist.xml | https://gitlab.com/es-de/emulationstation-de/-/blob/master/USERGUIDE.md |
| Libretro BIOS | https://docs.libretro.com/library/bios |
| XDG Base Dir Spec | https://specifications.freedesktop.org/basedir-spec/latest |
| pytest-qt | https://pytest-qt.readthedocs.io |
| py-spy | https://github.com/benfred/py-spy |

---

*v2.3 · KISS + Clean Code · 2026-05-17*
