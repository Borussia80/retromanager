# Handoff: Auditoria UX/UI · Retromanager

## Resumo

Este pacote é o resultado de uma **auditoria de UX/UI** feita sobre o app Retromanager (gerenciador de ROMs em Qt/Python, vide screenshots). Não é um redesenho do app inteiro: é um **plano de correções** com 17 achados pontuais, organizados por severidade e prioridade.

Sua tarefa, como desenvolvedor, é aplicar as correções descritas em `FIXES.md` no código-fonte existente do Retromanager, preservando a arquitetura atual (Qt/PySide ou similar — confirmar lendo o repositório).

## Como usar este pacote

1. **Abra `FIXES.md`** — é a lista exaustiva e ordenada das 17 correções, com IDs (A·01, B·02, etc.). Cada item tem: contexto do problema, arquivo provável onde corrigir, e descrição da solução esperada.
2. **Consulte `Auditoria UX-UI.html`** para ver o contexto visual: anotações sobre screenshots, antes/depois, matriz de prioridade. Abra no navegador.
3. **Use a pasta `screenshots/`** quando precisar visualizar o estado atual de uma tela específica antes de mexer no código.
4. **Use a pasta `redesign_references/`** para os 3 redesenhos hi-fi (diálogo de hash, janela de Opções, painel de Downloads). São HTMLs de referência — não código a copiar, mas comportamento e visual a reproduzir em Qt.

## Sobre os HTMLs deste pacote

Os arquivos `.html` são **referências de design**, criados pra mostrar intenção visual e comportamento.  
**Não** são código a ser copiado direto pro app. Você deve **reproduzir o design no ambiente nativo do Retromanager** — provavelmente Qt Widgets ou QML — usando os componentes, estilos e padrões já estabelecidos no projeto.

## Fidelidade

**Hi-fi**, mas focada em comportamento e tom mais do que em valores numéricos exatos.

- **Cores, tipografia e espaçamento** dos mockups são alinhados ao tema escuro atual do app, mas os tokens exatos devem vir do tema Qt já em uso no projeto.
- **Microcopy** (português, tom, capitalização) está finalizada — copiar literalmente.
- **Estados, layouts e fluxos** estão definidos em detalhe.

## Stack alvo (inferido dos screenshots)

- Aplicação desktop nativa (Linux confirmado pelo caminho `/home/rmilet/Jogos/ROMs`)
- Provavelmente **Qt** (PySide6 / PyQt6) — sinais: o label exposto `GroupBox`, botões com check `✓/✕`, estética geral dos diálogos
- Repositório: `github.com/Borussia80/retromanager`

Se a stack confirmada for outra, adaptar os arquivos `.ui`/`.qml`/widgets equivalentes.

## Prioridade sugerida

Implementar em 3 sprints, na ordem do `FIXES.md`:

| Sprint   | Foco                          | Itens                                   |
| -------- | ----------------------------- | --------------------------------------- |
| Sprint 1 | Tirar a poeira (~ 3 dias)     | A·01, A·02, A·03, D·02, F·01, F·02, F·03, C·02, C·03 |
| Sprint 2 | Reconstruir fluxos centrais   | B·01, B·02, B·03, E·01, E·02, C·01, G·01, G·03 |
| Sprint 3 | Tornar utilizável de verdade  | D·01, G·02, D·03                        |

## Arquivos neste pacote

```
design_handoff_retromanager_audit/
├── README.md                       ← este arquivo
├── FIXES.md                        ← lista detalhada das 17 correções (a tarefa)
├── Auditoria UX-UI.html            ← relatório visual completo
├── screenshots/                    ← 15 capturas do estado atual
└── redesign_references/            ← 3 mockups Antes/Depois extraídos
```

## Como invocar o Claude Code

Sugestão de prompt inicial dentro do repositório do Retromanager:

> Li o pacote `design_handoff_retromanager_audit/`. Comece pelo Sprint 1 do `FIXES.md`. Antes de mudar código, liste os arquivos `.ui`, `.qml`, `.py` e `.ts` (Qt translations) que você vai precisar tocar para cada item. Aguarde minha confirmação antes de aplicar as mudanças.
