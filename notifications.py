import shutil
import subprocess

from PyQt6.QtCore import QObject


class Notifier(QObject):
    """Send desktop notifications via notify-send (freedesktop.org spec)."""

    def send(self, title: str, body: str, icon: str = "") -> None:
        if not shutil.which("notify-send"):
            return
        cmd = ["notify-send", "-a", "RetroManager"]
        if icon:
            cmd += ["-i", icon]
        cmd += [title, body]
        try:
            subprocess.Popen(cmd)
        except FileNotFoundError:
            pass
