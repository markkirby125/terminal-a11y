import os
import sys
import pytest
from io import StringIO
from terminal_a11y.photophobia import PhotophobiaFilter, AmberPalette
from terminal_a11y.color import ColorLevel

class MockStream(StringIO):
    def isatty(self):
        return True

def test_photophobia_disabled_with_no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    stream = MockStream()
    filter = PhotophobiaFilter(stream)
    
    assert filter.disabled is True
    filter.write("\x1b[36mCyan text\x1b[0m")
    assert stream.getvalue() == "\x1b[36mCyan text\x1b[0m"

def test_photophobia_truecolor_mapping(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("COLORTERM", "truecolor")
    
    stream = MockStream()
    filter = PhotophobiaFilter(stream)
    
    assert filter.disabled is False
    assert filter.color_level == ColorLevel.TRUECOLOR
    
    # Write a string with bright cyan
    filter.write("Normal \x1b[96mCyan text\x1b[0m")
    
    # Should start with TrueColor Amber palette, replace \x1b[96m with TrueColor FG,
    # and \x1b[0m with RESET + BG + FG
    output = stream.getvalue()
    
    assert output.startswith(AmberPalette.TRUECOLOR_BG + AmberPalette.TRUECOLOR_FG)
    assert AmberPalette.TRUECOLOR_FG in output
    assert AmberPalette.RESET in output

def test_photophobia_sixteen_color_mapping(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("COLORTERM", raising=False)
    monkeypatch.delenv("WT_SESSION", raising=False)
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    monkeypatch.setenv("TERM", "xterm")
    monkeypatch.setenv("FORCE_COLOR", "1") # Force to 16
    
    stream = MockStream()
    filter = PhotophobiaFilter(stream)
    
    assert filter.disabled is False
    # write something without colors
    filter.write("Hello")
    output = stream.getvalue()
    assert output == AmberPalette.SIXTEEN_BG + AmberPalette.SIXTEEN_FG + "Hello"

def test_photophobia_close_emits_reset(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("COLORTERM", raising=False)
    monkeypatch.delenv("WT_SESSION", raising=False)
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    monkeypatch.setenv("TERM", "xterm")
    stream = MockStream()
    filter = PhotophobiaFilter(stream)
    filter.write("Hello")
    assert AmberPalette.SIXTEEN_BG in stream.getvalue()
    filter.close()
    output = stream.getvalue()
    assert output.endswith(AmberPalette.RESET)
