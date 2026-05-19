# Changelog

Todas as mudanças notáveis do projeto estão documentadas aqui.  
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [2.3.11] - 2026-05-19

### Corrigido
- `DownloadEngine`: sinal `progress` agora carrega `rom_name` como primeiro argumento — elimina o padrão `_active_rom_name` em `mainwindow.py` que, com downloads concorrentes, atualiza o painel sempre com o último ROM iniciado em vez do que realmente está progredindo
- `_platforms.py`: tokens FTS5 agora têm `"` escapado como `""` antes de entrar na query `MATCH`; previne `OperationalError` em buscas com aspas ou caracteres especiais
- `download_queue.py`: `_onpbDeleteClicked` não lança `IndexError` quando a seleção é removida entre o clique e o handler — guarda adicionada

---

## [2.3.10] - 2026-05-19

### Refatorado
- `DownloadEngine` reescrito com `QThreadPool` + `QRunnable` em vez de `QThread` manual por ROM — elimina toda a classe de crashes `QThread: Destroyed while thread is still running` pela raiz. O pool gerencia o ciclo de vida dos threads automaticamente; não há mais dicts `_active_threads`/`_active_workers`, `_retry_schedule`, `_pending_retry_count` nem lógica de GC manual

---

## [2.3.9] - 2026-05-18

### Corrigido
- `DownloadEngine`: corrige `QThread: Destroyed while thread is still running` ao baixar — quando todos os downloads completavam antes de um timer de retry disparar, o engine emitia `finished` e era destruído; ao disparar, o retry criava um thread órfão que era coletado pelo GC enquanto ainda rodava. Solução: `_pending_retry_count` impede a emissão de `finished` enquanto há timers de retry pendentes
- `DownloadEngine`: referências Python a `DownloadWorker` agora são mantidas até o thread filho terminar completamente (movido `_active_workers.pop` para `_on_thread_done`), evitando que o GC destrua o worker enquanto o thread ainda está em execução

---

## [2.3.8] - 2026-05-18

### Corrigido
- `_addToQueue`: nas views pseudo-plataforma (Favoritos, Recentes, Baixados), a plataforma real é lida do campo `UserRole` de cada linha em vez do item selecionado na barra lateral; evita erro "ROM não encontrada no catálogo" ao tentar baixar via essas views
- `ThumbnailFetcher`: mantém referência Python ao objeto até a conclusão do pool para evitar GC prematuro que destruía `fetcher.signals` e cortava as conexões de sinal — corrige thumbnails não aparecendo na grade

---

## [2.3.7] - 2026-05-18

### Corrigido
- Crash `QThread: Destroyed while thread is still running` ao baixar ROMs com retry: o timer de retry era agendado antes do thread anterior terminar, sobrescrevendo `_active_threads` e deixando o GC destruir o thread em execução. O timer agora é agendado em `_on_thread_done`, após o thread estar completamente parado

---

## [2.3.6] - 2026-05-18

### Corrigido
- Crash ao clicar em Baixar: `QPainterPath.addRoundedRect` exige `QRectF`; `QRect.adjusted()` retornava `QRect`, causando `TypeError` ao repintar qualquer card da grade

---

## [2.3.5] - 2026-05-18

### Corrigido
- RetroArch: exibe aviso com nome da core e instruções de instalação quando a core não está presente, em vez de lançar sem `-L` silenciosamente
- `refresh-cache.sh`: corrige TypeError por argumento extra passado ao `CacheGenerator`
- Plataformas Sony PlayStation, PlayStation 2 e PSP agora aparecem após atualizar o catálogo

---

## [2.3.4] - 2026-05-18

### Corrigido
- Verificação automática de atualizações agora habilitada por padrão em novas instalações
- Typo `LASTEST` → `LATEST` em `UpdaterHelper` (atributos e método `latestVersionString`)
- Exceções silenciosas em `_platforms.py` e `retroarch_helper.py` agora emitem aviso no log

---

## [2.3.3] - 2026-05-16

### Adicionado
- Tela de splash ao iniciar o aplicativo

### Corrigido
- 7 correções de usabilidade e precisão no catálogo e no sistema de downloads
- Crash ao dar duplo clique no histórico de jogos
- Estado do botão de download incorreto em alguns cenários

---

## [2.3.2] - 2026-05-10

### Corrigido
- Source IDs das plataformas Sony ajustados para IDs corretos no Archive.org
- Formato CHD corrigido na detecção de arquivos Sony
- `QPixmapCache.find` e remoção de source IDs Sony inválidos

---

## [2.3.0] - 2026-04-28

### Adicionado
- Suporte às plataformas Sony PlayStation, PlayStation 2 e PSP
- Plugin RPCS3 para PlayStation 3
- Health check do banco de dados de plataformas
- Schema v2 do banco SQLite de catálogo
- Smart Collections (FEAT-005)
- Crash reporter integrado (OBS-002)
- Verificação de integridade de downloads (OBS-003)
- Download engine v2 com fila aprimorada (FEAT-001–009)
- Temas claro e escuro configuráveis
- Busca FTS5 com fallback Python
- Notificações de fim de download
- Diálogo de atualização com abertura do navegador na página de releases
- 97 testes automatizados; CI/CD com GitHub Actions
- Gerenciamento de memória (deleteLater, QPixmapCache 50 MB, desconexão no closeEvent)
- Pacotes AppImage e Flatpak

### Corrigido
- 10 bugs críticos do Sprint 0 (BUG-001–010)
- 3 gargalos de performance na UI detectados por stress test
- 5 problemas detectados pelo engineering-best-practices

### Melhorado
- Instrumentação de startup e profiling
- Refatoração de qualidade em todos os módulos principais

---

## [2.1.0] - 2026-04-10

### Adicionado
- Histórico de jogos recentes (recently played)
- Autocomplete na barra de busca
- Fuzzy search por subsequência
- Botão de retry em downloads com falha
- ETA no painel de download

### Corrigido
- Detecção de RetroArch e Lutris via wrappers Flatpak
- Crash ao fechar o aplicativo
- Dependências transitivas do pacote Flatpak (psutil, PyQt6-sip)
- Binários do host expostos corretamente dentro do sandbox Flatpak
- Remoção completa do branding NoIntro-Roms-Downloader

---

## [2.0.0] - 2026-03-20

### Adicionado
- Catálogo SQLite — substitui `database_cache.json`
- `RomEntry` como dataclass tipada com mypy
- Thumbnail LRU com limites de tamanho e contagem
- `ThumbnailFetcher` migrado para `QNetworkAccessManager`
- Pause/resume real no sistema de downloads
- Verificação de versão robusta via QNetworkAccessManager
- Empacotamento: AppImage (PyInstaller), Flatpak manifest + AppStream, XDG desktop entry
- GitHub Actions com pytest + ruff
- Logging estruturado com `RotatingFileHandler`
- Grade de ROMs virtualizada com `QListView` + delegate

### Corrigido
- Validação de membros 7z antes de extrair (path traversal)
- `DownloadWorker` usa `threading.Event` em vez de flag booleana
- Exibição de nome de região em pt-BR no empty state
