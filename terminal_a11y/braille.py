import re
import sys
import unicodedata
from typing import TextIO

__all__ = ["BRAILLE_WIDTH", "ascii_fallback", "wrap_braille", "BrailleFilter"]

BRAILLE_WIDTH = 40

# Common Unicode symbol -> ASCII replacements.
_SYMBOL_FALLBACKS = {
    "✓": "[OK]",
    "✔": "[OK]",
    "✗": "[X]",
    "✘": "[X]",
    "⚠": "[!]",
    "ℹ": "[i]",
    "★": "*",
    "☆": "*",
    "●": "*",
    "○": "o",
    "•": "*",
    "·": "*",
    "→": "->",
    "←": "<-",
    "⇒": "=>",
    "⇐": "<=",
    "↑": "^",
    "↓": "v",
    "—": "-",
    "–": "-",
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "…": "...",
    "−": "-",
    "×": "x",
    "÷": "/",
    "≈": "~",
    "≤": "<=",
    "≥": ">=",
    "≠": "!=",
    "∞": "inf",
    "©": "(c)",
    "®": "(r)",
    "™": "(tm)",
}

# Regex ranges covering many emoji and pictographic symbols.
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # geometric shapes extended
    "\U0001F800-\U0001F8FF"  # supplemental arrows
    "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
    "\U00002700-\U000027BF"  # dingbats
    "]+",
    flags=re.UNICODE,
)


def _is_symbolic(char: str) -> bool:
    """Return True if the character is a symbol or other unsupported glyph."""
    if char in _SYMBOL_FALLBACKS:
        return True
    category = unicodedata.category(char)
    # So = Symbol, other; Sk = Symbol, modifier; Sm = Symbol, math
    return category.startswith("S")


def ascii_fallback(text: str) -> str:
    """
    Replace Unicode symbols and emojis with ASCII equivalents.

    Unknown emojis are replaced with ``[emoji]`` so the output contains no
    unsupported glyphs.
    """
    # First, map known symbols so they are not swallowed by the emoji regex.
    chars: list[str] = []
    for char in text:
        if char in _SYMBOL_FALLBACKS:
            chars.append(_SYMBOL_FALLBACKS[char])
        else:
            chars.append(char)
    text = "".join(chars)

    # Replace remaining emoji/pictograph runs.
    text = _EMOJI_RE.sub(lambda m: "[emoji]", text)

    # Replace any leftover unsupported symbols.
    result: list[str] = []
    for char in text:
        if _is_symbolic(char):
            result.append("[sym]")
        else:
            result.append(char)
    return "".join(result)


def wrap_braille(text: str, width: int = BRAILLE_WIDTH) -> str:
    """
    Wrap text so that no line exceeds ``width`` characters.

    Performs ASCII fallback first, then wraps on word boundaries where
    possible. Long words are hard-wrapped.
    """
    text = ascii_fallback(text)
    lines: list[str] = []

    for raw_line in text.split("\n"):
        line = raw_line.rstrip()
        while len(line) > width:
            # Prefer breaking at a space.
            break_point = line.rfind(" ", 0, width + 1)
            if break_point <= 0:
                break_point = width
            chunk = line[:break_point].rstrip()
            lines.append(chunk)
            line = line[break_point:].lstrip()
        lines.append(line)

    return "\n".join(lines)


class BrailleFilter:
    """
    Stream filter that formats output for refreshable braille displays.
    """

    def __init__(self, stream: TextIO = sys.stdout, width: int = BRAILLE_WIDTH):
        self.stream = stream
        self.width = width
        self._buffer = ""

    def write(self, data: str) -> None:
        if not data:
            return
        self._buffer += data
        if "\n" in self._buffer:
            *chunks, self._buffer = self._buffer.split("\n")
            for chunk in chunks:
                self.stream.write(wrap_braille(chunk + "\n", self.width))

    def flush(self) -> None:
        if self._buffer:
            self.stream.write(wrap_braille(self._buffer, self.width))
            self._buffer = ""
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
