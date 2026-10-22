"""OCR backend (manga-ocr). Loaded lazily; the model downloads on first use."""
from __future__ import annotations

from PIL import Image


class Ocr:
    def __init__(self) -> None:
        self._engine = None

    def load(self) -> None:
        if self._engine is None:
            from manga_ocr import MangaOcr

            self._engine = MangaOcr()

    def read(self, image: Image.Image) -> str:
        self.load()
        return self._engine(image.convert("RGB")).strip()
