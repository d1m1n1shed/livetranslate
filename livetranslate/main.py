"""LiveTranslate entry point (run on Windows).

Hotkeys:
  Ctrl+Alt+J  crop a screen region -> OCR -> lookup
  Ctrl+Alt+C  look up the text currently in the clipboard (copy it first)
  Ctrl+Alt+B  show/hide the result panel
  Ctrl+Alt+Q  quit
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import mss
from PIL import Image
from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from pynput import keyboard

from . import translate
from .lookup import Analyzer
from .ocr import Ocr
from .ui import CropOverlay, ResultBar

HOTKEYS = {
    "crop": "<ctrl>+<alt>+q",
    "clip": "<ctrl>+<alt>+c",
    "toggle": "<ctrl>+<alt>+b",
    "quit": "<ctrl>+<alt>+j",
}


class Bridge(QObject):
    """Carries events from the pynput thread / workers to the Qt main thread."""

    crop = Signal()
    clip = Signal()
    toggle = Signal()
    quit = Signal()
    status = Signal(str)
    done = Signal(str, list, list, object)


class App:
    def __init__(self) -> None:
        self.qt = QApplication(sys.argv)
        self.qt.setQuitOnLastWindowClosed(False)
        icon = QIcon(str(Path(__file__).resolve().parent.parent / "assets" / "icon.ico"))
        self.qt.setWindowIcon(icon)
        self.tray = QSystemTrayIcon(icon, self.qt)
        self.tray.setToolTip("LiveTranslate  (Ctrl+Alt+Q = crop)")
        menu = QMenu()
        self.bar = ResultBar()
        self.settings = QSettings("LiveTranslate", "LiveTranslate")
        side = self.settings.value("sidebar", False, type=bool)
        self.bar.set_sidebar(side)
        self.act_side = menu.addAction("Sidebar mode (right edge)")
        self.act_side.setCheckable(True)
        self.act_side.setChecked(side)
        self.act_side.toggled.connect(self._set_sidebar)
        menu.addAction("Show / hide panel  (Ctrl+Alt+B)", self.bar.toggle)
        menu.addSeparator()
        menu.addAction("Quit", self.qt.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.bar.toggle() if r == QSystemTrayIcon.Trigger else None
        )
        self.tray.show()
        self.bridge = Bridge()
        self.ocr = Ocr()
        self.analyzer: Analyzer | None = None
        self.overlay: CropOverlay | None = None

        b = self.bridge
        b.crop.connect(self.start_crop)
        b.clip.connect(self.from_clipboard)
        b.toggle.connect(self.bar.toggle)
        b.quit.connect(self.qt.quit)
        b.status.connect(self.bar.show_status)
        b.done.connect(self.bar.show_result)

        self.hotkeys = keyboard.GlobalHotKeys(
            {
                HOTKEYS["crop"]: b.crop.emit,
                HOTKEYS["clip"]: b.clip.emit,
                HOTKEYS["toggle"]: b.toggle.emit,
                HOTKEYS["quit"]: b.quit.emit,
            }
        )
        threading.Thread(target=self._warmup, daemon=True).start()

    def _warmup(self) -> None:
        self.analyzer = Analyzer()
        self.ocr.load()

    def _get_analyzer(self) -> Analyzer:
        if self.analyzer is None:
            self.analyzer = Analyzer()
        return self.analyzer

    def _set_sidebar(self, on: bool) -> None:
        self.settings.setValue("sidebar", on)
        self.bar.set_sidebar(on)

    # --- actions -------------------------------------------------------
    def start_crop(self) -> None:
        with mss.mss() as sct:
            raw = sct.grab(sct.monitors[0])  # whole virtual desktop
        shot = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        self.overlay = CropOverlay(shot, (raw.left, raw.top))
        self.overlay.selected.connect(self._on_region)
        self.overlay.show()
        self.overlay.activateWindow()

    def _on_region(self, img: Image.Image) -> None:
        self.bridge.status.emit("Reading… (first run downloads the OCR model)")
        threading.Thread(target=self._work, args=(img, None), daemon=True).start()

    def from_clipboard(self) -> None:
        text = self.qt.clipboard().text().strip()
        if not text:
            self.bar.show_status("Clipboard is empty")
            return
        self.bridge.status.emit("Looking up…")
        threading.Thread(target=self._work, args=(None, text), daemon=True).start()

    def _work(self, img: Image.Image | None, text: str | None) -> None:
        try:
            if text is None:
                text = self.ocr.read(img)
            if not text:
                self.bridge.status.emit("No text recognised")
                return
            an = self._get_analyzer()
            sentence = None
            try:
                sentence = translate.translate_sentence(text)
            except Exception as e:  # online part is optional
                sentence = f"(translate failed: {e})"
            self.bridge.done.emit(text, an.words(text), an.kanji(text), sentence)
        except Exception as e:
            self.bridge.status.emit(f"Error: {e}")

    def run(self) -> int:
        self.hotkeys.start()
        print("LiveTranslate running. Ctrl+Alt+Q = crop, Ctrl+Alt+C = clipboard, Ctrl+Alt+J = quit")
        return self.qt.exec()


def main() -> None:
    sys.exit(App().run())


if __name__ == "__main__":
    main()
