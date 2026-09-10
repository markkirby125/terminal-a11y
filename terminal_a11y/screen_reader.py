import re

__all__ = ["TOKEN_MAP", "linearize", "format_header", "ScreenReaderFilter"]

TOKEN_MAP = {
    "✓": "[PASS]",
    "✔": "[PASS]",
    "✗": "[FAIL]",
    "✘": "[FAIL]",
    "⚠": "[WARN]",
    "ℹ": "[INFO]",
}

def linearize(text: str) -> str:
    """
    Strips carriage returns that cause screen reader buffer thrashing
    when used for spinners or progress bars. Converts symbols to textual tokens.
    """
    text = re.sub(r'\r\n?', '\n', text)
    
    for symbol, replacement in TOKEN_MAP.items():
        text = text.replace(symbol, replacement)
    
    return text

def format_header(text: str) -> str:
    """
    Formats a section header to be more distinct for screen readers.
    Strips visual decoration like === Header === and returns a clear text.
    """
    stripped = re.sub(r'^[\s\=\-\#\*]+|[\s\=\-\#\*]+$', '', text)
    if not stripped:
        return ""
    return f"*** {stripped} ***"

class ScreenReaderFilter:
    """
    Intercepts writes, strips carriage returns, converts symbols,
    and allows injecting terminal bells.
    """
    def __init__(self, stream):
        self.stream = stream

    def write(self, text: str):
        linearized = linearize(text)
        self.stream.write(linearized)

    def flush(self):
        self.stream.flush()

    def inject_bell(self):
        """Injects a \a bell on completion."""
        self.stream.write('\a')
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
