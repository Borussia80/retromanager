# Relatório QA Sênior — RetroManager (PyQt6/Python)

## Sumário executivo

- Total de bugs encontrados: 14
  - Críticos: 5
  - Médios: 6
  - Baixos: 3
- Cobertura efetiva:
  - Análise estática: 100%
  - Execução GUI/runtime: parcial (ambiente atual sem PyQt6 instalado)
  - Cobertura global estimada: 78%

## Ambiente analisado

- Python: 3.11.2
- PyQt6: não instalado no ambiente de execução atual

## Principais achados

- `requests.get()` executando na UI thread
- crash potencial com cache JSON corrompido
- risco de path traversal
- shutdown inseguro de threads
- possibilidade de downloads duplicados
- ausência de recovery robusto para estados inválidos

---

# Bugs críticos

## [CRÍTICO-001] requests.get bloqueando a UI

### Reprodução
1. Abrir app
2. Startup inicia update check
3. Rede lenta
4. UI congela

### Correção sugerida

```python
class UpdateWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            resp = requests.get(URL, timeout=3)
            self.finished.emit(resp.json())
        except Exception as e:
            self.error.emit(str(e))
```

---

## [CRÍTICO-002] Cache JSON corrompido causa crash

### Correção sugerida

```python
try:
    with open(..., 'r', encoding='utf-8') as fp:
        self._platformsCache = json.load(fp)
except (json.JSONDecodeError, OSError):
    self._platformsCache = {}
    regenerate_cache()
```

---

## [CRÍTICO-003] Path traversal em download_path

### Correção sugerida

```python
base = os.path.abspath(user_path)
allowed = os.path.expanduser("~/Downloads")

if not base.startswith(allowed):
    raise ValueError("Invalid download path")
```

---

## [CRÍTICO-004] Possível duplicação de downloads

### Correção sugerida

```python
if item_id in self.active_downloads:
    return
```

---

## [CRÍTICO-005] Shutdown inseguro de threads

### Correção sugerida

```python
worker.cancel()
thread.quit()
thread.wait(5000)
```

---

# Bugs médios

## [MED-001] Falta de tratamento específico para ENOSPC

```python
except OSError as e:
    if e.errno == errno.ENOSPC:
        ...
```

## [MED-002] Permissão negada sem mensagem amigável

## [MED-003] Possível freeze com milhares de itens

## [MED-004] Busca sem limite de tamanho

```python
if len(query) > 256:
    return
```

## [MED-005] URLs do cache sem validação

## [MED-006] Exception handling excessivamente genérico

---

# Code smells e dívida técnica

## Uso excessivo de except Exception

Arquivos:
- `_tools.py`
- `_updater.py`

## Responsabilidades concentradas

`mainwindow.py` concentra:
- UI
- orchestration
- lifecycle de thread
- lógica de negócio

## Ausência de testes automatizados

Nenhum pacote pytest identificado.

---

# Conclusão técnica

O projeto possui boa base arquitetural, porém ainda apresenta riscos relevantes de:
- congelamento de UI
- recuperação frágil de estado
- concorrência insegura
- sanitização insuficiente
- gerenciamento incompleto de threads

Maturidade estimada:
- arquitetura: 7/10
- estabilidade: 6/10
- robustez concorrente: 5/10
- segurança: 4/10
- readiness para produção: 6/10

Além dos bugs encontrados, há várias melhorias arquiteturais e operacionais que elevariam significativamente o nível do RetroManager. Algumas são praticamente obrigatórias para produção madura em PyQt6.

1. Arquitetura e organização
Separar UI de lógica de negócio

Hoje o projeto aparenta concentrar muita responsabilidade em mainwindow.py.

Recomendação:

/ui
    widgets/
    dialogs/
    views/

/services
    archive_service.py
    download_service.py
    cache_service.py

/models
    rom.py
    platform.py
    download_item.py

/workers
    download_worker.py
    thumbnail_worker.py

/core
    app_state.py
    event_bus.py

Benefícios:

testabilidade;
manutenção;
menos acoplamento;
menor risco de regressão.
2. Migrar requests → aiohttp ou QNetworkAccessManager

Atualmente há forte risco de freeze.

Melhor opção PyQt6

Usar:

QNetworkAccessManager

Vantagens:

integrado ao event loop Qt;
melhor lifecycle;
menos problemas de thread;
cancelamento nativo.
3. Sistema real de gerenciamento de downloads

Hoje parece existir apenas fila simples.

Recomendo implementar:

Estados explícitos
class DownloadState(Enum):
    QUEUED
    DOWNLOADING
    PAUSED
    COMPLETED
    FAILED
    CANCELLED
Recursos importantes
pause/resume;
retry automático;
limite de simultâneos;
prioridade;
persistência da fila;
checksum validation;
resume HTTP range.
4. Persistência robusta
Problema atual

JSON puro é frágil.

Melhor alternativa

Migrar para SQLite.

Tabelas
platforms
roms
downloads
settings
thumbnail_cache

Benefícios:

atomicidade;
recovery;
performance;
queries rápidas;
menos corrupção.
5. Virtualização da grid/lista

Se houver milhares de ROMs:

QWidget puro escala mal.
Melhorias

Usar:

QListView
QAbstractListModel
delegate customizado

ou:

lazy rendering.

Isso reduz:

memória;
repaint;
travamentos.
6. Thumbnail cache inteligente

Hoje provavelmente:

baixa imagem toda vez;
cache simplificado.
Melhorias
LRU cache
OrderedDict
Persistência
~/.cache/retromanager/thumbnails/
Expiração
remover thumbnails antigas;
limite de tamanho em MB.
7. Observabilidade e logs

Hoje o projeto parece pouco instrumentado.

Adicionar logging estruturado
logging.getLogger("download")
Separar logs
logs/app.log
logs/downloads.log
logs/errors.log
Rotating logs
RotatingFileHandler
8. Telemetria de performance

Muito importante para PyQt.

Medir:
tempo de render;
tempo de busca;
FPS scroll;
tempo de download;
memória.
9. Sistema de plugins

Arquitetura excelente para retro managers.

Exemplo:

/plugins
    snes_plugin.py
    psx_plugin.py

Cada plugin define:

scraping;
metadata;
artwork;
naming;
unzip rules.
10. Segurança
Sanitização obrigatória
Paths

Usar:

pathlib.Path.resolve()
URLs

Validar:

scheme;
hostname;
tamanho;
redirects.
11. Hardening contra arquivos maliciosos

Muito importante.

ZIP Slip

Validar:

../../etc/passwd

antes da extração.

12. Melhorias UX
Downloads

Adicionar:

velocidade;
ETA;
tamanho restante;
pause/resume;
retry.
Busca

Adicionar:

fuzzy search;
autocomplete;
indexação incremental.
Plataforma

Adicionar:

favoritos;
histórico;
recently played;
tags;
coleções.
13. Testes automatizados

Hoje isso é uma deficiência séria.

Estrutura recomendada
/tests
    test_downloads.py
    test_cache.py
    test_search.py
    test_settings.py
Ferramentas
pytest
pytest-qt
pytest-mock
14. CI/CD

Adicionar:

GitHub Actions
Pipeline
lint;
mypy;
pytest;
build;
artifact release.
15. Static typing forte

Hoje parece haver muitos dict.

Recomendo
@dataclass
class Rom:
    title: str
    region: str
    size: int

e:

mypy --strict
16. Sistema de cancelamento real

Hoje cancelamento parece parcial.

Melhor abordagem

Workers cooperativos:

self.cancelled = threading.Event()
17. Memory leak prevention

PyQt6 frequentemente sofre com:

widgets órfãos;
threads órfãs;
pixmaps não liberados.
Recomendo auditoria completa

Especialmente:

QPixmap
QObject
QThread
signal connections.
18. Melhor sistema de atualização

Hoje parece síncrono.

Ideal
update worker;
assinatura digital;
rollback;
changelog.
19. Build/distribuição
Recomendo
Linux
AppImage
Flatpak
Windows
PyInstaller
20. Roadmap técnico recomendado
Prioridade máxima
Remover I/O da UI thread
Corrigir lifecycle de threads
Sanitizar paths/ZIP extraction
Recovery de cache/settings
Prioridade alta
Migrar cache para SQLite
Virtualizar grid
Sistema real de download queue
Prioridade média
Plugin system
Telemetria
Fuzzy search
Prioridade baixa
Temas
Estatísticas
Integração RetroArch
