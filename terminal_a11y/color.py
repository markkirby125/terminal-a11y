import os
import sys
from enum import IntEnum

__all__ = ["ColorLevel", "get_color_level"]

class ColorLevel(IntEnum):
    NONE = 0
    SIXTEEN = 1
    TWO_FIFTY_SIX = 2
    TRUECOLOR = 3

def get_color_level(stream=None) -> ColorLevel:
    """
    Determine terminal color capabilities.
    Obeys NO_COLOR and FORCE_COLOR env vars.
    Checks COLORTERM, WT_SESSION, TERM_PROGRAM and TERM.
    """
    if stream is None:
        stream = sys.stdout

    if "NO_COLOR" in os.environ:
        return ColorLevel.NONE

    force_color = os.environ.get("FORCE_COLOR", "")
    is_tty = stream.isatty() if hasattr(stream, "isatty") else False

    if not is_tty and not force_color:
        return ColorLevel.NONE

    term_program = os.environ.get("TERM_PROGRAM", "")
    if term_program == "Apple_Terminal":
        return ColorLevel.TWO_FIFTY_SIX

    colorterm = os.environ.get("COLORTERM", "").lower()
    if colorterm in ("truecolor", "24bit"):
        return ColorLevel.TRUECOLOR

    if "WT_SESSION" in os.environ:
        return ColorLevel.TRUECOLOR

    if term_program == "iTerm.app":
        return ColorLevel.TRUECOLOR

    vte_version = os.environ.get("VTE_VERSION", "")
    if vte_version:
        try:
            if int(vte_version[:4]) >= 3600:
                return ColorLevel.TRUECOLOR
            else:
                return ColorLevel.TWO_FIFTY_SIX
        except ValueError:
            pass

    term = os.environ.get("TERM", "").lower()
    
    if "256color" in term:
        return ColorLevel.TWO_FIFTY_SIX
        
    if term in ("xterm", "screen", "tmux", "vt100", "rxvt", "color", "ansi", "cygwin", "linux"):
        return ColorLevel.SIXTEEN
        
    if os.name == 'nt':
        return ColorLevel.SIXTEEN

    if force_color:
        return ColorLevel.SIXTEEN

    return ColorLevel.NONE
