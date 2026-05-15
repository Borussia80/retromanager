# Referências de redesenho

Os 3 mockups "Antes / Depois" estão embutidos no arquivo `../Auditoria UX-UI.html`, na seção **"Como ficaria, depois."**.

Abra o HTML no navegador e role até essa seção para ver:

1. **Hash dialog** (correção C·01) — diff visual de hashes divergentes + ação "Re-baixar"
2. **Janela de Opções** (correções A·02, C·02, C·03) — sem `GroupBox`, com presets de cache, botão "Escolher…"
3. **Painel de Downloads** (correções E·01, E·02) — seções Baixando / Em fila / Concluídos, com progresso e ações

Os mockups são **renderizados em HTML/CSS** apenas como referência visual.
Reproduza o comportamento em Qt usando widgets nativos (`QDialog`, `QGroupBox`, `QProgressBar`, `QToolButton`).

Não copiar HTML/CSS literalmente para o app.
