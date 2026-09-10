import os
import sys
import re
from typing import TextIO

from terminal_a11y.color import get_color_level, ColorLevel
from terminal_a11y.ansi import SGR_PATTERN

__all__ = ["AmberPalette", "PhotophobiaFilter"]

class AmberPalette:
    TRUECOLOR_FG = "\x1b[38;2;255;176;0m"
    TRUECOLOR_BG = "\x1b[48;2;18;14;4m"
    
    TWO_FIFTY_SIX_FG = "\x1b[38;5;214m"
    TWO_FIFTY_SIX_BG = "\x1b[48;5;232m"
    
    SIXTEEN_FG = "\x1b[33m"
    SIXTEEN_BG = "\x1b[40m"

    RESET = "\x1b[0m"

class PhotophobiaFilter:
    def __init__(self, stream: TextIO = sys.stdout):
        self.stream = stream
        self._closed = False
        
        if "NO_COLOR" in os.environ:
            self.disabled = True
            return
            
        self.disabled = False
        self.color_level = get_color_level(stream)
        
        if self.color_level == ColorLevel.TRUECOLOR:
            self.fg = AmberPalette.TRUECOLOR_FG
            self.bg = AmberPalette.TRUECOLOR_BG
        elif self.color_level == ColorLevel.TWO_FIFTY_SIX:
            self.fg = AmberPalette.TWO_FIFTY_SIX_FG
            self.bg = AmberPalette.TWO_FIFTY_SIX_BG
        else:
            self.fg = AmberPalette.SIXTEEN_FG
            self.bg = AmberPalette.SIXTEEN_BG

        self.reset = AmberPalette.RESET

    def _replace_sgr(self, match):
        params = match.group(1).split(';')
        
        if not params or params == [''] or '0' in params:
            return self.reset + self.bg + self.fg
            
        is_bg = any(p.startswith('4') or p == '48' for p in params)
        is_fg = any(p.startswith('3') or p == '38' or p.startswith('9') for p in params)
        
        res = ""
        if is_bg:
            res += self.bg
        if is_fg:
            res += self.fg
            
        if not res:
            return match.group(0)
            
        return res

    def write(self, data: str):
        if self.disabled:
            self.stream.write(data)
            return

        if not hasattr(self, '_palette_initialized'):
            self.stream.write(self.bg + self.fg)
            self._palette_initialized = True

        filtered_data = SGR_PATTERN.sub(self._replace_sgr, data)
        self.stream.write(filtered_data)

    def flush(self):
        self.stream.flush()

    def close(self):
        if self._closed:
            return
        self._closed = True
        if hasattr(self, '_palette_initialized'):
            try:
                self.stream.write(self.reset)
                self.stream.flush()
            except (ValueError, OSError):
                # Stream may already be closed during interpreter shutdown.
                pass

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
