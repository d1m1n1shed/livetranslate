"""Qt widgets: region-select overlay and the result bar."""
from __future__ import annotations

from html import escape

from PIL import Image
from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QTextBrowser, QVBoxLayout, QWidget

from .lookup import KanjiInfo, WordInfo


def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    img = img.convert("RGBA")
    qimg = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimg.copy())


class CropOverlay(QWidget):
    """Full-desktop frozen screenshot; drag to select a region."""

    selected = Signal(object)  # PIL.Image
    cancelled = Signal()

    def __init__(self, shot: Image.Image, origin: tuple[int, int]) -> None:
        super().__init__()
        self._shot = shot
        self._pix = pil_to_qpixmap(shot)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setCursor(Qt.CrossCursor)
        # cover the whole virtual desktop (Qt logical coordinates)
        screens = QGuiApplication.screens()
        rect = screens[0].geometry()
        for s in screens[1:]:
            rect = rect.united(s.geometry())
        self.setGeometry(rect)
        self._start: QPoint | None = None
        self._cur: QPoint | None = None

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.drawPixmap(self.rect(), self._pix)
        p.fillRect(self.rect(), QColor(0, 0, 0, 90))
        if self._start and self._cur:
            r = QRect(self._start, self._cur).normalized()
            p.drawPixmap(r, self._pix, self._src_rect(r))
            p.setPen(QPen(QColor("#4fc3f7"), 2))
            p.drawRect(r)

    def _src_rect(self, r: QRect) -> QRect:
        sx = self._pix.width() / self.width()
        sy = self._pix.height() / self.height()
        return QRect(int(r.x() * sx), int(r.y() * sy), int(r.width() * sx), int(r.height() * sy))

    def mousePressEvent(self, e) -> None:
        self._start = self._cur = e.position().toPoint()

    def mouseMoveEvent(self, e) -> None:
        self._cur = e.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, e) -> None:
        if not self._start:
            return
        r = QRect(self._start, e.position().toPoint()).normalized()
        self.close()
        if r.width() < 5 or r.height() < 5:
            self.cancelled.emit()
            return
        s = self._src_rect(r)
        self.selected.emit(self._shot.crop((s.x(), s.y(), s.x() + s.width(), s.y() + s.height())))

    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key_Escape:
            self.close()
            self.cancelled.emit()


CSS = """
body { color:#eee; font-family:'Yu Gothic UI','Meiryo',sans-serif; font-size:14px; }
.src { font-size:20px; margin-bottom:6px; }
.w { margin:2px 0; } .rd { color:#ffb74d; } .gl { color:#bbb; }
.k { font-size:18px; color:#4fc3f7; } .h { color:#81c784; margin-top:8px; font-weight:bold; }
"""


class ResultBar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("background:#1e1e24; border:1px solid #4fc3f7; border-radius:6px;")
        self._status = QLabel("")
        self._status.setStyleSheet("color:#aaa; border:none; padding:2px 6px;")
        self._view = QTextBrowser()
        self._view.setStyleSheet("border:none; background:transparent;")
        self._view.document().setDefaultStyleSheet(CSS)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.addWidget(self._status)
        lay.addWidget(self._view)
        self._drag: QPoint | None = None
        self.sidebar = False
        self._has_content = False
        self.resize(560, 420)

    def set_sidebar(self, on: bool) -> None:
        """Sidebar: docked to the right screen edge, full height, never steals focus."""
        self.sidebar = on
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, on)
        if self.isVisible():
            self.place()

    def toggle(self) -> None:
        if self.isVisible():
            self.hide()
        elif self._has_content:
            self._present()
        else:
            self.show_status("Nothing yet - press Ctrl+Alt+J to capture")

    def _present(self) -> None:
        self.place()
        self.show()
        self.raise_()
        if not self.sidebar:
            self.activateWindow()

    def place(self) -> None:
        geo = QApplication.primaryScreen().availableGeometry()
        if self.sidebar:
            w = 400
            self.setGeometry(geo.right() - w + 1, geo.top(), w, geo.height())
        else:
            self.resize(560, 420)
            self.move(geo.center().x() - self.width() // 2, geo.top() + 20)

    def show_status(self, msg: str) -> None:
        self._status.setText(msg)
        self._view.clear()
        self._present()

    def show_result(
        self,
        text: str,
        words: list[WordInfo],
        kanji: list[KanjiInfo],
        sentence: str | None = None,
    ) -> None:
        h = [f"<div class='src'>{escape(text)}</div>"]
        if sentence:
            h.append(f"<div>{escape(sentence)}</div>")
        h.append("<div class='h'>Words</div>")
        for w in words:
            rd = f" <span class='rd'>【{escape(w.reading)}】</span>" if w.reading != w.surface else ""
            lem = f" <span class='gl'>({escape(w.lemma)})</span>" if w.lemma != w.surface else ""
            gl = escape(" / ".join(w.glosses)) if w.glosses else "—"
            h.append(f"<div class='w'><b>{escape(w.surface)}</b>{rd}{lem}<br><span class='gl'>{gl}</span></div>")
        if kanji:
            h.append("<div class='h'>Kanji</div>")
            for k in kanji:
                h.append(
                    f"<div class='w'><span class='k'>{escape(k.char)}</span> "
                    f"{escape(', '.join(k.meanings))}<br>"
                    f"<span class='rd'>音 {escape('、'.join(k.on))}　訓 {escape('、'.join(k.kun))}</span></div>"
                )
        self._status.setText("Esc or Ctrl+Alt+B to hide" if self.sidebar else "Esc to hide, drag to move")
        self._view.setHtml("".join(h))
        self._has_content = True
        self._present()

    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key_Escape:
            self.hide()

    def mousePressEvent(self, e) -> None:
        if self.sidebar:
            return
        self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e) -> None:
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, _e) -> None:
        self._drag = None
