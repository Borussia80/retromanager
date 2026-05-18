# Logo Retromanager · Pacote de Assets

Marca em **pixel-art** (5×7 por letra) na configuração **RE / TR** empilhada, em **âmbar `#F5A524` + creme `#F6EFDE`** sobre slate escuro. Bitmap puro — escala perfeito de 16px a 512px sem perda.

---

## Estrutura

```
retromanager_logo_assets/
├── README.md                      ← este arquivo
├── png/
│   ├── icon/                      ← App icons (tile arredondado + gradiente laranja)
│   │   ├── icon_16.png            (16×16)
│   │   ├── icon_24.png
│   │   ├── icon_32.png
│   │   ├── icon_48.png
│   │   ├── icon_64.png
│   │   ├── icon_128.png
│   │   ├── icon_256.png
│   │   └── icon_512.png
│   ├── tray/                      ← System tray / status bar (mono âmbar, transparente)
│   │   ├── tray_16.png
│   │   ├── tray_22.png            (GTK status icon)
│   │   └── tray_24.png            (Plasma system tray)
│   ├── mark/                      ← Marca isolada bicolor (transparente, sem tile)
│   │   ├── mark_64.png
│   │   ├── mark_128.png
│   │   ├── mark_256.png
│   │   └── mark_512.png
│   ├── wordmark.png               ← Marca + "RETROMANAGER" lado a lado
│   └── about_dialog.png           ← Versão otimizada pro QDialog Sobre (~64h)
├── ico/
│   └── retromanager.ico           ← Multi-resolução Windows (16/32/48/64/128/256)
└── svg/
    ├── icon.svg                   ← Versão completa com tile laranja
    ├── mark.svg                   ← Marca sem outline
    └── mark_outlined.svg          ← Marca com outline escuro
```

---

## Onde instalar no Retromanager

### 1 · Ícone da aplicação Qt (todas as janelas)

Adicione em `mainwindow.py` (ou onde o `QApplication` é criado):

```python
from PyQt6.QtGui import QIcon, QPixmap

# ... dentro do __init__ ou main()
icon = QIcon()
for size in (16, 24, 32, 48, 64, 128, 256, 512):
    icon.addPixmap(QPixmap(f"resources/icons/icon_{size}.png"))
QApplication.setWindowIcon(icon)
```

Copie os PNGs de `png/icon/` para `resources/icons/` (ou onde o projeto já carrega assets).

### 2 · Janela "Sobre"

No `about.py`, substituir a imagem atual do U-Haul truck:

```python
# Antes:
# self.lbl_pic.setPixmap(QPixmap("resources/img/truck.png"))

# Depois:
self.lbl_pic.setPixmap(QPixmap("resources/icons/icon_64.png"))
# ou, para mostrar marca + nome lado a lado:
# self.lbl_pic.setPixmap(QPixmap("resources/icons/about_dialog.png"))
```

Recomendado: use `about_dialog.png` (já tem marca + wordmark no formato horizontal).

### 3 · System tray (se F·01 introduzir indicador na status bar)

Para o indicador discreto na status bar (sugerido na auditoria F·01):

```python
from PyQt6.QtGui import QIcon

tray_icon = QIcon("resources/icons/tray_16.png")
# usar em status bar ou QSystemTrayIcon
```

Tamanhos: **16** (Windows tray), **22** (GTK), **24** (KDE Plasma).

### 4 · `.desktop` file (Linux)

No arquivo `retromanager.desktop`:

```
[Desktop Entry]
Type=Application
Name=Retromanager
Comment=Gerenciador de biblioteca de jogos retro
Exec=retromanager
Icon=retromanager
Categories=Game;Utility;
```

Copiar o **`icon_256.png`** renomeado pra `retromanager.png` em:
- `/usr/share/icons/hicolor/256x256/apps/retromanager.png`
- e/ou todos os tamanhos hicolor (16, 22, 24, 32, 48, 64, 128, 256, 512) — basta copiar cada `icon_N.png` pra `hicolor/NxN/apps/retromanager.png`.

Ou, mais simples, copiar `svg/icon.svg` pra `/usr/share/icons/hicolor/scalable/apps/retromanager.svg`.

### 5 · Windows (build futuro)

Use `ico/retromanager.ico` no `.spec` do PyInstaller ou no `setup.py`:

```python
# pyinstaller
# pyinstaller --icon=retromanager_logo_assets/ico/retromanager.ico ...
```

### 6 · README do GitHub

No `README.md` do projeto:

```markdown
<img src="docs/wordmark.png" alt="Retromanager" width="540" />
```

Copie `png/wordmark.png` pra `docs/wordmark.png`.

---

## Especificação da marca

| Item               | Valor                                                |
| ------------------ | ---------------------------------------------------- |
| Grid por letra     | 5 colunas × 7 linhas                                 |
| Gap entre letras   | 1 px lógico (incluso no bitmap)                      |
| Gap entre linhas   | 1 px lógico                                          |
| Cores              | `#F5A524` âmbar · `#F6EFDE` creme · `#0A0F1C` outline |
| Tile do app icon   | Gradiente `#FFB84A → #D97706` (135°), raio 22%       |
| App icon (≤32 px)  | Sem outline (espaço insuficiente)                    |
| App icon (≥48 px)  | Com outline 1 px escuro                              |
| Letras no app icon | Ambas em **cream** (RE e TR) — máxima legibilidade   |
| Letras no mark/dark| RE em âmbar, TR em cream (bicolor original)          |
| Tray icon          | Mono âmbar solid, sem outline, sem tile              |

---

## Tarefa para o Claude Code

> Os arquivos em `retromanager_logo_assets/` substituem o logo atual do app (caminhão laranja). Instale-os conforme as instruções da seção "Onde instalar no Retromanager" acima:
>
> 1. Crie a pasta `resources/icons/` no projeto.
> 2. Copie todos os PNGs relevantes pra dentro.
> 3. Atualize `mainwindow.py` pra setar o `QApplication.setWindowIcon` com múltiplas resoluções.
> 4. Atualize `about.py` pra usar `icon_64.png` ou `about_dialog.png` no lugar do truck.
> 5. Se houver `.desktop` file ou ícones em `/usr/share/icons`, atualize-os (mas apenas se já estiverem no controle de versão — não mexa em paths do sistema).
> 6. Faça um commit por categoria: `feat(brand): adiciona logo pixel-art RETR` separado de `feat(brand): substitui ícone no diálogo Sobre`.
>
> Não copie todos os tamanhos pra dentro do binário — escolha apenas os necessários (16, 32, 48, 64, 128, 256, 512 para o ícone; 16/22/24 para tray se for usar).

---

## Direitos

Marca criada para o projeto Retromanager.
Licença: mesma do projeto (MIT).
