"""
Bootstrap utilities: startup timing, crash reporter, and optional memory profiling.

StartupTimer is always active — marks are stored and reported via the logger.
Memory profiling (tracemalloc + objgraph) is only useful when invoked explicitly,
typically when DEBUG=4 is set before launching the app.
Call install_crash_hook() once in app.pyw to catch unhandled exceptions.
"""

import logging
import sys
import time
import traceback

log = logging.getLogger("retromanager.bootstrap")


class StartupTimer:
    """Measures wall-clock time of each startup phase and logs a summary at INFO."""

    _marks: dict[str, float] = {}

    @classmethod
    def mark(cls, label: str) -> None:
        cls._marks[label] = time.perf_counter()
        start = cls._marks.get("_start", cls._marks[label])
        log.debug("startup · %-28s → %6.0f ms", label, (cls._marks[label] - start) * 1000)

    @classmethod
    def report(cls) -> None:
        start = cls._marks.get("_start", 0.0)
        log.info("=== Startup timing report ===")
        for label, t in cls._marks.items():
            log.info("  %-30s %6.0f ms", label, (t - start) * 1000)


def start_memory_profiling() -> None:
    """Start tracemalloc (25 stack frames). No-op if already tracing."""
    import tracemalloc
    if not tracemalloc.is_tracing():
        tracemalloc.start(25)
        log.debug("tracemalloc started — 25 stack frames")


def snapshot_memory(label: str = "") -> None:
    """Log top-15 allocators by source line. No-op if tracemalloc is not running."""
    import tracemalloc
    if not tracemalloc.is_tracing():
        return
    snapshot = tracemalloc.take_snapshot()
    top = snapshot.statistics("lineno")[:15]
    tag = f": {label}" if label else ""
    log.debug("=== Memory snapshot%s ===", tag)
    for stat in top:
        log.debug("  %s", stat)


def install_crash_hook() -> None:
    """Install sys.excepthook to log crashes and show a user-friendly dialog (OBS-002)."""
    _crash_log = logging.getLogger("retromanager.crash")

    def _excepthook(exc_type, exc_value, exc_tb):
        _crash_log.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton
            from PyQt6.QtCore import Qt
            app = QApplication.instance()
            if app:
                dlg = QDialog()
                dlg.setWindowTitle("RetroManager — Erro inesperado")
                dlg.setMinimumSize(600, 400)
                lay = QVBoxLayout(dlg)
                lbl = QLabel("O RetroManager encontrou um erro inesperado e precisa fechar.\n"
                             "O erro foi registrado em ~/.cache/retromanager/logs/errors.log")
                lbl.setWordWrap(True)
                lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
                tb_edit = QTextEdit()
                tb_edit.setReadOnly(True)
                tb_edit.setPlainText(tb_text)
                tb_edit.setStyleSheet("font-family: monospace; font-size: 11px;")
                btn = QPushButton("Fechar")
                btn.clicked.connect(dlg.accept)
                lay.addWidget(lbl)
                lay.addWidget(tb_edit, 1)
                lay.addWidget(btn)
                dlg.exec()
        except Exception as e:
            _crash_log.debug("crash dialog failed to display: %s", e)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook


def check_leaks() -> None:
    """Log object-type growth since last call.

    Call this after navigating between platforms — a growing type count
    with no corresponding shrink is a candidate memory leak.
    Requires: pip install objgraph
    """
    try:
        import objgraph
        log.debug("=== Object growth (objgraph) ===")
        # show_growth prints to stdout; acceptable for an interactive debug utility
        objgraph.show_most_common_types(limit=10)
        objgraph.show_growth(limit=10)
    except ImportError:
        log.debug("objgraph not available — run: pip install objgraph")
