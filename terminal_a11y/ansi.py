import re

__all__ = ["ANSI_PATTERN", "SGR_PATTERN", "strip_ansi"]

ANSI_PATTERN = re.compile(
    r'\x1b\[[0-?]*[ -/]*[@-~]'
    r'|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)'
    r'|\x1b[@-Z\\-_]'
    r'|[\x80-\x9F]',
    re.DOTALL
)
SGR_PATTERN = re.compile(r'\x1b\[([0-9;]*)m')

def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape sequences from a string.
    Strips complex 24-bit SGR codes, cursor positioning, spinners, etc.
    """
    return ANSI_PATTERN.sub('', text)
