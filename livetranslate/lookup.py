"""Japanese text analysis: tokenise, readings, dictionary + kanji lookup (offline)."""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field

import fugashi
import pykakasi
from jamdict import Jamdict

KANJI_RE = re.compile(r"[一-鿿々]")
SKIP_POS = {"補助記号", "空白", "記号"}
NO_GLOSS_POS = {"助詞", "助動詞"}  # particles/auxiliaries: dictionary hits are misleading


@dataclass
class WordInfo:
    surface: str
    lemma: str
    reading: str  # hiragana
    pos: str
    glosses: list[str] = field(default_factory=list)


@dataclass
class KanjiInfo:
    char: str
    meanings: list[str]
    on: list[str]
    kun: list[str]


def _kata_to_hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


class Analyzer:
    def __init__(self) -> None:
        self._tagger = fugashi.Tagger()
        self._kks = pykakasi.kakasi()
        self._local = threading.local()  # sqlite connections are per-thread

    @property
    def _jam(self) -> Jamdict:
        if not hasattr(self._local, "jam"):
            self._local.jam = Jamdict()
        return self._local.jam

    def _reading(self, surface: str, kana: str | None) -> str:
        if kana and kana != "*":
            return _kata_to_hira(kana)
        return "".join(item["hira"] for item in self._kks.convert(surface))

    def _glosses(self, lemma: str, surface: str, limit: int = 4) -> list[str]:
        for key in (lemma, surface):
            if not key:
                continue
            res = self._jam.lookup(key, lookup_chars=False)
            if res.entries:
                out: list[str] = []
                for sense in res.entries[0].senses[:limit]:
                    out.append("; ".join(g.text for g in sense.gloss[:3]))
                return out
        return []

    def words(self, text: str) -> list[WordInfo]:
        result: list[WordInfo] = []
        for tok in self._tagger(text):
            f = tok.feature
            if f.pos1 in SKIP_POS or not tok.surface.strip():
                continue
            lemma = (getattr(f, "lemma", None) or tok.surface).split("-")[0]
            kana = getattr(f, "kana", None)
            # reading of the surface form (inflected), falling back to kakasi
            reading = self._reading(tok.surface, kana)
            result.append(
                WordInfo(
                    tok.surface,
                    lemma,
                    reading,
                    f.pos1,
                    [] if f.pos1 in NO_GLOSS_POS else self._glosses(lemma, tok.surface),
                )
            )
        return result

    def kanji(self, text: str) -> list[KanjiInfo]:
        seen: list[str] = []
        for c in text:
            if KANJI_RE.match(c) and c not in seen:
                seen.append(c)
        out: list[KanjiInfo] = []
        for c in seen:
            res = self._jam.lookup(c, lookup_ne=False)
            if not res.chars:
                out.append(KanjiInfo(c, [], [], []))
                continue
            ch = res.chars[0]
            on, kun = [], []
            for grp in ch.rm_groups:
                for r in grp.readings:
                    if r.r_type == "ja_on":
                        on.append(r.value)
                    elif r.r_type == "ja_kun":
                        kun.append(r.value)
            out.append(KanjiInfo(c, ch.meanings(english_only=True)[:5], on, kun))
        return out
