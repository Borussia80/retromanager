# Changelog

Todas as mudanças notáveis do projeto estão documentadas aqui.  
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

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
