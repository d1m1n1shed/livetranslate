"""Optional online sentence translation. Disabled by default.

Set LIVETRANSLATE_ONLINE=1 and ANTHROPIC_API_KEY to enable (needs `pip install anthropic`).
"""
from __future__ import annotations

import os


def enabled() -> bool:
    return os.environ.get("LIVETRANSLATE_ONLINE") == "1" and bool(os.environ.get("ANTHROPIC_API_KEY"))


def translate_sentence(text: str) -> str | None:
    if not enabled():
        return None
    import anthropic

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=512,
        messages=[{"role": "user", "content": f"Translate this Japanese to English. Output only the translation.\n\n{text}"}],
    )
    return msg.content[0].text.strip()
