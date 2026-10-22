# LiveTranslate

Windows desktop helper for reading Japanese on screen. Press a hotkey, drag a box around any text
(including text inside images that can't be selected), and get each word with its hiragana reading and
English meaning, plus on'yomi / kun'yomi / meaning for every kanji. Everything runs offline.

โปรแกรมแปลภาษาบนหน้าจอ เน้นคันจิ: กดคีย์ลัด ลากเลือกพื้นที่ (รวมถึงข้อความในรูปภาพ) แล้วแสดงคำอ่านและความหมาย

## Hotkeys

| Keys | Action |
|---|---|
| Ctrl+Alt+Q | Crop a screen region -> OCR -> lookup |
| Ctrl+Alt+C | Look up the text in the clipboard |
| Ctrl+Alt+B | Show / hide the result panel |
| Ctrl+Alt+J | Quit |

Tray icon menu: **Sidebar mode** docks the panel to the right screen edge (remembered between runs).

## Install (Windows, Python 3.10)

```bat
py -3.10 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

The dictionary database `jamdict.db` should be at `%USERPROFILE%\.jamdict\data\jamdict.db`.
`pip install jamdict-data` fails on some Windows setups (file lock while unpacking); if so, download the
`jamdict-data` sdist from PyPI, extract `jamdict.db.xz` and decompress it to that path.
The OCR model (~850 MB) downloads automatically on first run.

Run: `run.bat` (uses `.venv` in this folder).

## Optional online sentence translation

`pip install anthropic`, then set `LIVETRANSLATE_ONLINE=1` and `ANTHROPIC_API_KEY`. Off by default.

## Credits

- OCR: [manga-ocr](https://github.com/kha-white/manga-ocr) (Apache-2.0)
- Tokenizer: [fugashi](https://github.com/polm/fugashi) + UniDic
- Dictionary data: [JMdict / KANJIDIC2](https://www.edrdg.org/) via [jamdict](https://github.com/neocl/jamdict),
  licensed CC BY-SA 4.0 by the Electronic Dictionary Research and Development Group
- UI: Qt for Python (PySide6, LGPL)

## License

MIT for this project's code (see `LICENSE`). Dictionary data and models keep their own licenses.
