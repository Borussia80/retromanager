# Correções — Retromanager

17 itens. IDs estáveis (use em commits / PRs: `fix(ui): A·01 elimina strings em inglês no diálogo de erro`).

Severidade: 🔴 Crítico · 🟠 Importante · 🔵 Sugestão

---

## Sprint 1 — Tirar a poeira

### A·01 🔴 Diálogos misturam pt-BR e inglês

**Onde:** todos os `QDialog` (`*.ui`, `*.qml`) + sistema de tradução Qt (`*.ts` / `*.qm`).

**Problema:** "Download failed" + "Tentar novamente" na mesma janela. "Cache & Database / Miscellaneous" em inglês na janela de Opções, etc.

**Fix:**
- Extrair todas as strings de UI com `tr()` ou `QObject::tr()`.
- Gerar `pt_BR.ts` com `pylupdate6` / `lupdate`.
- Traduzir 100% das strings; compilar com `lrelease`.
- Manter `en_US.ts` se quiser oferecer EN — mas **uma janela ≠ dois idiomas**.

**Strings prioritárias (pt-BR final):**
- "Download failed" → "Falha no download"
- "Connection timed out after 60s" → "Tempo limite excedido (60s)"
- "Cache & Database" → "Cache e biblioteca"
- "Miscellaneous" → "Comportamento"
- "Decompress after download" → "Descompactar após baixar"
- "Check updates at startup" → "Buscar atualizações ao iniciar"
- "Cache validity (in days)" → "Atualizar catálogo a cada (dias)"
- "Download path" → "Pasta de download"
- "Cancel" → "Cancelar"
- "Released under the MIT License." → "Distribuído sob a licença MIT."

---

### A·02 🔴 Label `GroupBox` exposto na UI

**Onde:** janela Opções, segundo bloco (`options.ui` ou equivalente).

**Problema:** o título do `QGroupBox` ficou com o valor default do Qt Designer.

**Fix:**
- Renomear para **"Pasta de download"** (ou "Local de download").
- Fazer um grep no projeto inteiro: `groupBox`, `label_\d`, `pushButton_\d`, `frame_\d`. Listar e renomear todos os títulos default que estiverem visíveis.

```bash
grep -rn 'title="GroupBox\|title="Frame\|title="Form"' .
```

---

### A·03 🟠 Diálogo "Sobre" em inglês

**Onde:** `about.ui` ou `about_dialog.py`.

**Fix:**
- Subtítulo: "Retro game library manager" → **"Gerenciador de biblioteca de jogos retro"**
- Descrição:  
  > Navegue e baixe ROMs de jogos retro diretamente do archive.org. Suporta 17+ plataformas, incluindo NES, SNES, N64, Game Boy, Sega, Atari, PC Engine, Neo Geo MVS e arcade MAME.
- "Released under the MIT License." → "Distribuído sob a licença MIT."
- Nome do app: capitalizar para **"Retromanager"** (não `retromanager`). Padronizar em todo o app, incluindo `setApplicationName()`.

---

### D·02 🔴 Cabeçalhos da tabela truncados

**Onde:** `QTableView` / `QTreeView` que lista ROMs.

**Problema:** "JOGO" aparece como "OGO", "FORMATO" como "ORMAT".

**Fix:**
- Definir largura mínima por coluna no `QHeaderView`:
  ```python
  header = self.romTable.horizontalHeader()
  header.setMinimumSectionSize(80)
  header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.Interactive)
  header.setSectionResizeMode(COL_SIZE, QHeaderView.ResizeMode.ResizeToContents)
  ```
- Larguras mínimas sugeridas:
  - Jogo: 240 px (stretch)
  - Tamanho: 100 px
  - Formato: 70 px
  - MD5/SHA1: 240 px (ocultas por padrão — ver D·02b)
  - CRC32: 90 px
- Cabeçalho não deve cortar nunca: usar elipse só no conteúdo das linhas.

**D·02b** — As colunas técnicas (MD5/CRC32/SHA1) devem ficar **ocultas por default**, atrás de um item de menu **Ver → Mostrar hashes** ou um toggle no canto da tabela.

---

### F·01 🔴 Painel "INTEGRAÇÕES" no rodapé do sidebar

**Onde:** `sidebar.ui` / widget esquerdo da `mainwindow.ui`. Bloco com `RetroArch` e `Lutris`.

**Problema:** texto "Não encontrado" vermelho parece erro permanente.

**Fix:**
- **Remover o bloco da sidebar.**
- Criar uma nova aba **"Integrações"** dentro da janela Opções, com:
  - Linha por integração: nome, status (`Ativo` verde · `Não configurado` cinza), botão "Configurar…".
  - Detecção automática + campo para path manual (caso instalação custom).
- Se quiser indicador permanente, adicionar **só quando ativo**, num canto discreto da status bar: `RetroArch ✓` em verde-acinzentado.

---

### F·02 🟠 Pluralização incorreta e palavra redundante na sidebar

**Onde:** delegate / model da sidebar de plataformas + status bar.

**Problema:** "1 títulos", "Nenhum ainda", "14,769 títulos" inconsistentes. Status bar usa "itens".

**Fix:**
- Padronizar palavra: **"itens"** em todo o app.
- Função de plural:
  ```python
  def fmt_count(n):
      if n == 0: return "vazio"
      if n == 1: return "1 item"
      return f"{n:,} itens".replace(",", ".")
  ```
- Na sidebar, mostrar **só o número** alinhado à direita, em cinza secundário, sem palavra. A palavra aparece só em tooltip ou status bar.

---

### F·03 🔵 Badge "64" → "N64"

**Onde:** mapa de badges de plataforma (provável dicionário `PLATFORM_BADGES` ou similar).

**Fix:** trocar `"nintendo_64": "64"` por `"nintendo_64": "N64"`. Revisar outros — se "FDS" estiver ambíguo, manter mas adicionar tooltip com nome completo.

---

### C·02 🟠 Aviso vermelho gritante na janela Opções

**Onde:** mesmo `options.ui`.

**Problema:** texto em ALL-CAPS vermelho, em inglês, com typo ("recommanded"), referenciando valor inexistente ("&lt;none&gt;").

**Fix:** substituir o `QLineEdit` numérico + texto vermelho por um `QComboBox` com presets:

```
Atualizar catálogo:
  ◉ A cada 30 dias (recomendado)
  ◯ A cada 7 dias
  ◯ A cada 90 dias
  ◯ Toda inicialização (uso intenso de rede)
  ◯ Nunca (modo offline)
```

Sem helper text agressivo. Se "Toda inicialização" for selecionada, mostrar toast informativo no save.

---

### C·03 🔵 Botão de browse aparece como `.`

**Onde:** options.ui, linha "Download path".

**Fix:**
- Texto do botão: **"Escolher…"** (com reticências, indicando que abre diálogo).
- Ou usar `QToolButton` com ícone `folder-open` do tema do sistema + tooltip "Escolher pasta de downloads".
- Habilitar drop de pastas via `setAcceptDrops(True)` no `QLineEdit`.

---

## Sprint 2 — Reconstruir fluxos centrais

### B·01 🔴 Filtro de região sem resultados deixa tela em branco

**Onde:** `rom_list_view.py` (ou nome equivalente), tratamento de modelo vazio.

**Fix:**
- Detectar `rowCount() == 0` após aplicar filtro.
- Renderizar um widget **EmptyState** centralizado no lugar da tabela:
  - Ícone (search-off ou similar do tema)
  - Título: **"Nenhum ROM com tag USA em MAME"**
  - Descrição: "Os ROMs do MAME raramente carregam tag de região. Tente outra plataforma ou remova o filtro."
  - Botão primário: **"Mostrar todas as regiões"** (volta para "All")

Aproveitar pra mostrar **chips removíveis** acima da lista com os filtros ativos: `[USA ✕] [Não-protótipo ✕]`.

---

### B·02 🟠 Estados vazios inconsistentes — criar componente único

**Onde:** novo widget `EmptyState` reutilizável.

**Fix:**
- Criar `widgets/empty_state.py` com `EmptyState(icon, title, description, action_label, action_callback)`.
- Substituir todos os atuais:
  - **Inicial** (sem plataforma selecionada): ícone "gamepad" · "Bem-vindo ao Retromanager" · "Escolha uma plataforma à esquerda para começar."
  - **Favoritos vazio**: ícone "star-off" · "Sem favoritos ainda" · "Clique com o botão direito em um jogo e escolha **Favoritar**."
  - **Busca sem match**: ícone "search-off" · "Nada encontrado" · "Tente outros termos ou limpe a busca." · Ação: "Limpar busca"
  - **Filtro de região vazio**: ver B·01.
- Quando empty state estiver ativo, **esconder o cabeçalho da tabela** (`setHeaderHidden(True)` temporário ou trocar widget visível com `QStackedWidget`).

---

### B·03 🟠 "Mostrando 500 de 14.769" sem mostrar nada

**Onde:** lógica de paginação / chunking da lista.

**Fix:**
- **Sempre exibir** a primeira página (mínimo 500 itens), com scroll virtual.
- Banner sticky no topo da tabela quando `total > visíveis`:
  > ⓘ Mostrando 500 de 14.769 ROMs. **Refine a busca** ou [carregue todos].
- Botão "Carregar todos" carrega tudo (com mini-spinner) e some.

---

### E·01 🟠 Fila de downloads sem progresso/tamanho/velocidade

**Onde:** `download_queue_widget.py` e modelo da fila.

**Fix:** redesenhar painel com 4 seções verticais:

1. **Baixando · N** (0–3 itens, conforme `max_parallel`)
2. **Em fila · N**
3. **Concluídos · N** (recolhível, mostrando últimos 10)
4. **Com erro · N**

Cada item:
```
[ Nome amigável · shortname pequeno ]
[ tamanho · % · velocidade · ETA      ]
[ ███████████████░░░░░░░░ 64%        ]
[ × Cancelar  ↑ Prioridade  📂 Abrir  ]
```

Vide referência visual em `redesign_references/queue_after.html`.

---

### E·02 🔵 Botão azul sem rótulo no header do painel

**Onde:** mesmo widget.

**Fix:** substituir botão único por **trio de ações** (`QToolButton` com ícones do tema):
- ⏸ Pausar tudo (Ctrl+P)
- ▶ Retomar tudo
- 🗑 Limpar concluídos

Todos com tooltip + atalho de teclado.

---

### C·01 🟠 Diálogo de hash sem diff visual

**Onde:** `hash_verify_dialog.py` ou similar.

**Fix:**
- Cabeçalho mais informativo: "**Falha na verificação** · 2 de 3 algoritmos divergem"
- Para cada hash:
  - Algoritmo (MD5/SHA1/CRC32), valor calculado, ✓ ou ✕
  - Quando ✕: linha extra logo abaixo com hash **esperado**, em verde, prefixo "esp."
  - **Diff por caractere**: destacar com background os trechos divergentes em ambas linhas.
- Cada hash tem botão "copiar".
- Ação primária mudaria conforme caso:
  - Sucesso: `[OK]` apenas
  - Falha: `[Manter arquivo]` `[Re-baixar]` (primário)

Implementação do diff: comparar char-a-char e wrap em `<span style="background:...">` se for QLabel rich-text, ou usar `QTextDocument` com formatação.

Vide `redesign_references/hash_after.html`.

---

### G·01 🔵 View toggles sem ícone claro

**Onde:** topo da lista de ROMs.

**Fix:**
- Trocar ícones atuais por ícones claros:
  - **Lista**: ☰ (linhas horizontais)
  - **Grade**: ▦ (grade de quadrados)
- `QButtonGroup` exclusivo; selecionado tem background do accent, não-selecionado só borda.
- Remover o separador vertical "|" entre eles.
- Tooltips: "Vista em lista (Ctrl+1)" / "Vista em grade (Ctrl+2)".

---

### G·03 🔵 Campo de busca sem affordances padrão

**Onde:** input de busca no topo.

**Fix:**
- Ícone de lupa à esquerda (via `setAction(..., QLineEdit.LeadingPosition)`).
- Ação de limpar (×) à direita quando texto não vazio.
- Placeholder curto: **"Buscar ROMs…"**. Tirar a lista longa.
- Atalho discreto: dica `⌘F` / `Ctrl+F` à direita (em cinza).
- Foco no input quando o usuário digitar `/` (atalho tipo Gmail/GitHub) — opcional.

---

## Sprint 3 — Tornar utilizável de verdade

### D·01 🔴 Substituir MAME shortnames por nomes amigáveis

**Onde:** pipeline de ingestão de metadados.

**Problema:** lista mostra `005`, `100lions`, `10yard`, `1942` — nomes de arquivo, não de jogo.

**Fix:**
- Para MAME: parsear `mame.xml` (`mame -listxml`) ou usar o `gamename.dat` do progettoSnaps. Cada `<machine name="dkong">` tem `<description>Donkey Kong (US set 1)</description>`, `<year>1981</year>`, `<manufacturer>Nintendo</manufacturer>`.
- Cachear localmente em SQLite/JSON, indexado por shortname.
- Para consoles (NES, SNES, etc.): usar No-Intro / Redump DAT-o-MATIC; nomes já são amigáveis na maioria.
- Para Atari/Game Boy: ScreenScraper.fr ou TGDB como fallback opcional (com chave de API do usuário).

Modelo da lista passa a ter:
| Jogo (amigável)         | Shortname (secundário) | Ano  | Fabricante  | Tamanho | … |
| ----------------------- | ---------------------- | ---- | ----------- | ------- | - |
| 10-Yard Fight           | 10yard                 | 1983 | Irem        | 148.9 KB|   |
| 100 Lions               | 100lions               | 2007 | Aristocrat  | 10.8 MB |   |

Busca por título e shortname; mostrar match destacado.

---

### G·02 🔵 Painel de detalhes do ROM

**Onde:** painel direito da janela principal (substituir o painel de Downloads quando não há fila ativa, OU adicionar como `QSplitter` inferior).

**Fix:** ao selecionar uma linha, mostrar:
- Capa (placeholder cinza se ausente — **não inventar SVG**)
- Nome amigável grande + ano · fabricante
- Descrição (do scraper ou XML)
- Hashes esperados (pré-download)
- Botão **Baixar** primário
- Link "Abrir no archive.org →"
- Botão "★ Favoritar"

Painel direito vira `QStackedWidget` alternando entre **Detalhes** (quando nada está baixando) e **Fila** (quando há downloads ativos), com aba ou toggle pra forçar uma das duas vistas.

---

### D·03 🔵 Coluna "Formato" redundante

**Onde:** tabela.

**Fix:**
- Se 95%+ dos itens são `.zip`, remover a coluna.
- Mover info para a coluna de tamanho: `"10.8 MB · zip"` (sufixo discreto em monospace cinza).
- Mostrar badge só quando formato ≠ padrão da plataforma (ex: `.chd` para arcade, `.iso` para PSX).

Coluna liberada vira **Ano** ou **Fabricante** (vide D·01).

---

## Notas finais

- **Não introduzir novas dependências** sem checar com o mantenedor — preferir bibliotecas Qt nativas ou stdlib Python.
- **Commits por achado**, prefixados com o ID: `fix(ui): F·01 move painel de Integrações para a janela Opções`.
- **Antes de cada sprint**, validar com o mantenedor que os arquivos identificados como alvo realmente são os corretos.
- **Capturar antes/depois** ao terminar cada item: o mantenedor pode anexar nas notas da release.
