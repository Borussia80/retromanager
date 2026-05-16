#!/usr/bin/env bash
# RetroManager — profiling helper (PERF-002)
#
# Hotspots obrigatórios a medir (ver roadmap PERF-002):
#   _onListwidgetSelectionChanged — carregamento de ROMs na sidebar
#   _applyTableFilter             — cada keystroke na busca
#   GameTitleDelegate.paint       — repaint de cada célula (debug=4 → log de lentidão)
#   scan_downloaded               — scan do filesystem
#   _mame_names.load              — parse/load do cache MAME
#
# Uso:
#   scripts/profile.sh install         # instala ferramentas
#   scripts/profile.sh flame           # flame graph interativo (py-spy)
#   scripts/profile.sh cpu             # cProfile → profile.out
#   scripts/profile.sh mem             # scalene CPU+memória linha a linha
#   DEBUG=4 scripts/profile.sh cpu     # com startup marks e slow-paint logs

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/app.pyw"
OUT_DIR="$ROOT/scripts"

case "${1:-help}" in
  install)
    echo "Instalando ferramentas de profiling..."
    pip install py-spy scalene objgraph
    ;;

  flame)
    echo "Gerando flame graph com py-spy..."
    echo "(pressione Ctrl+C para parar a gravação)"
    SVG="$OUT_DIR/profile.svg"
    py-spy record -o "$SVG" -- python "$APP"
    echo "Salvo em: $SVG"
    ;;

  cpu)
    echo "Executando cProfile..."
    OUT="$OUT_DIR/profile.out"
    python -m cProfile -o "$OUT" "$APP"
    echo "Salvo em: $OUT"
    python - <<PSTATS
import pstats
p = pstats.Stats("$OUT")
p.sort_stats("cumulative")
p.print_stats(20)
PSTATS
    ;;

  mem)
    echo "Executando scalene (CPU + memória linha a linha)..."
    scalene "$APP"
    ;;

  hotspots)
    # Profile completo com startup marks e slow-paint logging
    echo "Executando com DEBUG=4 + cProfile..."
    OUT="$OUT_DIR/hotspots.out"
    DEBUG=4 python -m cProfile -o "$OUT" "$APP"
    python - <<PSTATS
import pstats
p = pstats.Stats("$OUT")
p.sort_stats("cumulative")
p.print_stats(25)
PSTATS
    ;;

  *)
    echo "Uso: $0 {install|flame|cpu|mem|hotspots}"
    echo ""
    echo "  install    Instala: py-spy, scalene, objgraph"
    echo "  flame      Flame graph via py-spy (requer permissão ptrace)"
    echo "  cpu        cProfile → profile.out (mostra top-20 funções)"
    echo "  mem        scalene: CPU + memória linha a linha"
    echo "  hotspots   cProfile com DEBUG=4 (startup marks + slow paints)"
    ;;
esac
